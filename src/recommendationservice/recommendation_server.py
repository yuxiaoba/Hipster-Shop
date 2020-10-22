#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import random
import time
import traceback
from concurrent import futures

import googleclouddebugger
import googlecloudprofiler
from google.auth.exceptions import DefaultCredentialsError
import grpc

import demo_pb2
import demo_pb2_grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

from logger import getJSONLogger
from opentelemetry import trace
from opentelemetry.instrumentation.grpc import server_interceptor
from opentelemetry.instrumentation.grpc.grpcext import intercept_server
from opentelemetry.instrumentation.grpc import client_interceptor
from opentelemetry.instrumentation.grpc.grpcext import intercept_channel
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter import jaeger
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.sdk.trace.export import Span, SpanExporter, SpanExportResult
from opentelemetry.exporter.jaeger import _translate_to_jaeger
from opentelemetry.exporter.jaeger.gen.jaeger import Collector as jaegerType

trace.set_tracer_provider(TracerProvider())
# create a JaegerSpanExporter
jaeger_exporter = jaeger.JaegerSpanExporter(
    service_name="recommendationservice",
    # configure agent
    # agent_host_name="localhost",
    # agent_port=6831,
    # optional: configure also collector
    collector_host_name=os.environ.get('JAEGER_HOST', 'jaeger-collector'),
    collector_port=14268,
    collector_endpoint="/api/traces?format=jaeger.thrift",
    # username=xxxx, # optional
    # password=xxxx, # optional
)


def new_export(spans):
    global jaeger_exporter
    self = jaeger_exporter
    jaeger_spans = _translate_to_jaeger(spans)
    podIp = os.environ.get('POD_IP')
    podName = os.environ.get('POD_NAME')
    nodeName = os.environ.get('NODE_NAME')
    tags = [
        jaegerType.Tag(
            key="exporter", vType=jaegerType.TagType.STRING, vStr="jaeger"),
        jaegerType.Tag(
            key="float", vType=jaegerType.TagType.DOUBLE, vDouble=312.23),
        jaegerType.Tag(
            key="ip", vType=jaegerType.TagType.STRING, vStr=podIp),
        jaegerType.Tag(
            key="name", vType=jaegerType.TagType.STRING, vStr=podName),
        jaegerType.Tag(key="node_name",
                       vType=jaegerType.TagType.STRING, vStr=nodeName)
    ]

    batch = jaegerType.Batch(
        spans=jaeger_spans,
        process=jaegerType.Process(
            serviceName=self.service_name, tags=tags),
    )

    if self.collector is not None:
        self.collector.submit(batch)
    self.agent_client.emit(batch)

    return SpanExportResult.SUCCESS

jaeger_exporter.export = new_export

# create a BatchExportSpanProcessor and add the exporter to it
span_processor = BatchExportSpanProcessor(jaeger_exporter)

# add to the tracer factory
trace.get_tracer_provider().add_span_processor(span_processor)

logger = getJSONLogger('recommendationservice-server')


def initStackdriverProfiling():
    project_id = None
    try:
        project_id = os.environ["GCP_PROJECT_ID"]
    except KeyError:
        # Environment variable not set
        pass

    for retry in xrange(1, 4):
        try:
            if project_id:
                googlecloudprofiler.start(service='recommendation_server', service_version='1.0.0', verbose=0,
                                          project_id=project_id)
            else:
                googlecloudprofiler.start(service='recommendation_server', service_version='1.0.0', verbose=0)
            logger.info("Successfully started Stackdriver Profiler.")
            return
        except (BaseException) as exc:
            logger.info("Unable to start Stackdriver Profiler Python agent. " + str(exc))
            if (retry < 4):
                logger.info("Sleeping %d seconds to retry Stackdriver Profiler agent initialization" % (retry * 10))
                time.sleep(1)
            else:
                logger.warning("Could not initialize Stackdriver Profiler after retrying, giving up")
    return


class RecommendationService(demo_pb2_grpc.RecommendationServiceServicer):
    def ListRecommendations(self, request, context):
        max_responses = 5
        # fetch list of products from product catalog stub
        cat_response = product_catalog_stub.ListProducts(demo_pb2.Empty())
        product_ids = [x.id for x in cat_response.products]
        filtered_products = list(set(product_ids) - set(request.product_ids))
        num_products = len(filtered_products)
        num_return = min(max_responses, num_products)
        # sample list of indicies to return
        indices = random.sample(range(num_products), num_return)
        # fetch product ids from indices
        prod_list = [filtered_products[i] for i in indices]
        logger.info("[Recv ListRecommendations] product_ids={}".format(prod_list))
        # build and return response
        response = demo_pb2.ListRecommendationsResponse()
        response.product_ids.extend(prod_list)
        return response

    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)


if __name__ == "__main__":
    logger.info("initializing recommendationservice")

    port = os.environ.get('PORT', "8080")
    catalog_addr = os.environ.get('PRODUCT_CATALOG_SERVICE_ADDR', '')
    if catalog_addr == "":
        raise Exception('PRODUCT_CATALOG_SERVICE_ADDR environment variable not set')
    logger.info("product catalog address: " + catalog_addr)

    channel = grpc.insecure_channel(catalog_addr)
    channel = intercept_channel(channel, client_interceptor())
    product_catalog_stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)

    # create gRPC server
    #server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
    #                     interceptors=(tracer_interceptor,))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # OpenTelemetry magic!
    server = intercept_server(server, server_interceptor())

    # add class to gRPC server
    service = RecommendationService()
    demo_pb2_grpc.add_RecommendationServiceServicer_to_server(service, server)
    health_pb2_grpc.add_HealthServicer_to_server(service, server)

    # start server
    logger.info("listening on port: " + port)
    server.add_insecure_port('[::]:' + port)
    server.start()

    # keep alive
    try:
        while True:
            time.sleep(10000)
    except KeyboardInterrupt:
        server.stop(0)
