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

from concurrent import futures
import argparse
import os
import sys
import time
import grpc
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateError
from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import DefaultCredentialsError

import demo_pb2
import demo_pb2_grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc
# import googleclouddebugger
import googlecloudprofiler
from logger import getJSONLogger

from opentelemetry import trace
from opentelemetry.instrumentation.grpc import server_interceptor
from opentelemetry.instrumentation.grpc.grpcext import intercept_server
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter import jaeger
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.sdk.trace.export import Span, SpanExporter, SpanExportResult
from opentelemetry.exporter.jaeger import _translate_to_jaeger
from opentelemetry.exporter.jaeger.gen.jaeger import Collector as jaegerType

trace.set_tracer_provider(TracerProvider())
# create a JaegerSpanExporter
jaeger_exporter = jaeger.JaegerSpanExporter(
    service_name="emailservice",
    # configure agent
    #agent_host_name="localhost",
    #agent_port=6831,
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
		jaegerType.Tag(key="exporter", vType=jaegerType.TagType.STRING, vStr="jaeger"),
		jaegerType.Tag(key="float", vType=jaegerType.TagType.DOUBLE, vDouble=312.23),
		jaegerType.Tag(key="ip", vType=jaegerType.TagType.STRING, vStr=podIp),
		jaegerType.Tag(key="name", vType=jaegerType.TagType.STRING, vStr=podName),
		jaegerType.Tag(key="node_name", vType=jaegerType.TagType.STRING, vStr=nodeName)
	]

	batch = jaegerType.Batch(
		spans=jaeger_spans,
		process=jaegerType.Process(serviceName=self.service_name, tags=tags),
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


logger = getJSONLogger('emailservice-server')
# Loads confirmation email template from file
env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('confirmation.html')


class BaseEmailService(demo_pb2_grpc.EmailServiceServicer):
    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)


class EmailService(BaseEmailService):
    def __init__(self):
        raise Exception('cloud mail client not implemented')
        super().__init__()

    @staticmethod
    def send_email(client, email_address, content):
        response = client.send_message(
            sender=client.sender_path(project_id, region, sender_id),
            envelope_from_authority='',
            header_from_authority='',
            envelope_from_address=from_address,
            simple_message={
                "from": {
                    "address_spec": from_address,
                },
                "to": [{
                    "address_spec": email_address
                }],
                "subject": "Your Confirmation Email",
                "html_body": content
            }
        )
        logger.info("Message sent: {}".format(response.rfc822_message_id))

    def SendOrderConfirmation(self, request, context):
        email = request.email
        order = request.order

        try:
            confirmation = template.render(order=order)
        except TemplateError as err:
            context.set_details("An error occurred when preparing the confirmation mail.")
            logger.error(err.message)
            context.set_code(grpc.StatusCode.INTERNAL)
            return demo_pb2.Empty()

        try:
            EmailService.send_email(self.client, email, confirmation)
        except GoogleAPICallError as err:
            context.set_details("An error occurred when sending the email.")
            print(err.message)
            context.set_code(grpc.StatusCode.INTERNAL)
            return demo_pb2.Empty()

        return demo_pb2.Empty()


class DummyEmailService(BaseEmailService):
    def SendOrderConfirmation(self, request, context):
        logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))
        return demo_pb2.Empty()


class HealthCheck():
    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)


def start(dummy_mode):
    #server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),
    #                    interceptors=(tracer_interceptor,))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # OpenTelemetry magic!
    server = intercept_server(server, server_interceptor())

    service = None
    if dummy_mode:
        service = DummyEmailService()
    else:
        raise Exception('non-dummy mode not implemented yet')

    demo_pb2_grpc.add_EmailServiceServicer_to_server(service, server)
    health_pb2_grpc.add_HealthServicer_to_server(service, server)

    port = os.environ.get('PORT', "8080")
    logger.info("listening on port: " + port)
    server.add_insecure_port('[::]:' + port)
    server.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


def initStackdriverProfiling():
    project_id = None
    try:
        project_id = os.environ["GCP_PROJECT_ID"]
    except KeyError:
        # Environment variable not set
        pass

    for retry in range(1, 4):
        try:
            if project_id:
                googlecloudprofiler.start(service='email_server', service_version='1.0.0', verbose=0,
                                          project_id=project_id)
            else:
                googlecloudprofiler.start(service='email_server', service_version='1.0.0', verbose=0)
            logger.info("Successfully started Stackdriver Profiler.")
            return
        except (BaseException) as exc:
            logger.info("Unable to start Stackdriver Profiler Python agent. " + str(exc))
            if (retry < 4):
                logger.info("Sleeping %d to retry initializing Stackdriver Profiler" % (retry * 10))
                time.sleep(1)
            else:
                logger.warning("Could not initialize Stackdriver Profiler after retrying, giving up")
    return


if __name__ == '__main__':
    logger.info('starting the email service in dummy mode.')

    start(dummy_mode=True)
