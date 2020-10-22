// Copyright 2018 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using cartservice.cartstore;
using cartservice.interfaces;
using CommandLine;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using System.Net;
using System.Security.Authentication;
using Microsoft.AspNetCore.Connections.Features;
using Grpc.Core;
using Microsoft.Extensions.Configuration;

namespace cartservice
{
    class Program
    {
        const string CART_SERVICE_ADDRESS = "LISTEN_ADDR";
        const string CART_SERVICE_PORT = "PORT";

        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("Invalid number of arguments supplied");
                Environment.Exit(-1);
            }

            switch (args[0])
            {
                case "start":
                    Console.WriteLine($"Started as process with id {System.Diagnostics.Process.GetCurrentProcess().Id}");

                    // Set hostname/ip address
                    Console.WriteLine($"Reading host address from {CART_SERVICE_ADDRESS} environment variable");
                    string hostname = Environment.GetEnvironmentVariable(CART_SERVICE_ADDRESS);
                    if (string.IsNullOrEmpty(hostname))
                    {
                        Console.WriteLine($"Environment variable {CART_SERVICE_ADDRESS} was not set. Setting the host to 0.0.0.0");
                        hostname = "0.0.0.0";
                    }

                    // Set the port
                    Console.WriteLine($"Reading cart service port from {CART_SERVICE_PORT} environment variable");
                    string portStr = Environment.GetEnvironmentVariable(CART_SERVICE_PORT);
                    int port;
                    if (string.IsNullOrEmpty(portStr))
                    {
                        Console.WriteLine($"{CART_SERVICE_PORT} environment variable was not set. Setting the port to 8080");
                        // TODO:DEBUG
                        // port = 8080;
                        port = 7070;
                    }
                    else
                    {
                        port = int.Parse(portStr);
                    }
                    Console.WriteLine($"Trying to start a grpc server at  {hostname}:{port}");
                    Console.WriteLine("Insecure mode!");
                    string[] warpperArgs = new string[args.Length + 1];
                    args.CopyTo(warpperArgs, 0);
                    Host.CreateDefaultBuilder(args).ConfigureWebHostDefaults(webBuilder =>
                    {
                        webBuilder.UseStartup<Startup>();
                        webBuilder.ConfigureKestrel(serverOptions =>
                        {
                            serverOptions.Listen(IPAddress.Parse(hostname), port, listenOptions =>
                            {
                                listenOptions.Protocols = HttpProtocols.Http2;
                            });
                        });

                        // webBuilder.UseUrls($"http://{hostname}:{port}");
                    }).Build().Run();
                    break;

                default:
                    Console.WriteLine("Invalid command");
                    break;
            }
        }
    }
}
