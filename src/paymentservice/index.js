/*
 * Copyright 2018 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use strict';

// require('@google-cloud/profiler').start({
//   serviceContext: {
//     service: 'paymentservice',
//     version: '1.0.0'
//   }
// });
// require('@google-cloud/trace-agent').start();
// require('@google-cloud/debug-agent').start({
//   serviceContext: {
//     service: 'paymentservice',
//     version: 'VERSION'
//   }
// });

const { NodeTracerProvider } = require('@opentelemetry/node');
const { SimpleSpanProcessor } = require('@opentelemetry/tracing');
const { JaegerExporter } =  require('@opentelemetry/exporter-jaeger');

const options = {
  serviceName: 'paymentservice',
  tags: [{key: 'ip', value: process.env.POD_IP},
    {key: 'name', value: process.env.POD_NAME},
    {key: 'node_name', value: process.env.NODE_NAME}], // optional
  host: process.env.JAEGER_HOST,
  port: process.env.JAEGER_PORT, // optional
  maxPacketSize: 65000 // optional
}

const exporter = new JaegerExporter(options);
const provider = new NodeTracerProvider();

provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
provider.register();
console.log("zipkin tracing initialized");

const path = require('path');
const HipsterShopServer = require('./server');

const PORT = process.env['PORT'];
const PROTO_PATH = path.join(__dirname, '/proto/');

const server = new HipsterShopServer(PROTO_PATH, PORT);

server.listen();
