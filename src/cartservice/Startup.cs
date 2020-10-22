using System;
using System.Collections.Generic;
using cartservice.cartstore;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using OpenTelemetry.Trace;

namespace cartservice
{
    public class Startup
    {
        public IConfiguration Configuration { get; }

        public Startup(IConfiguration configuration)
        {
            this.Configuration = configuration;
        }


        // This method gets called by the runtime. Use this method to add services to the container.
        // For more information on how to configure your application, visit https://go.microsoft.com/fwlink/?LinkID=398940
        public void ConfigureServices(IServiceCollection services)
        {
            // services.AddSingleton<ICartStore>();
            services.AddGrpc();
            services.AddSingleton<CartStore>();

            services.AddOpenTelemetryTracerProvider(telemetry =>
            {
                telemetry.AddJaegerExporter((jaegerOptions) =>
                {
                    jaegerOptions.ServiceName = "cartservice";
                    jaegerOptions.AgentHost = this.Configuration.GetValue<string>("JAEGER_HOST");
                    jaegerOptions.AgentPort = this.Configuration.GetValue<int>("JAEGER_PORT");
                    jaegerOptions.ProcessTags = new Dictionary<string, object>{
                        {"exporter","jaeger"},
                        {"float", 312.23},
                        {"ip",this.Configuration.GetValue<string>("POD_IP")},
                        {"podName",this.Configuration.GetValue<string>("POD_NAME")},
                        {"nodeName",this.Configuration.GetValue<string>("NODE_NAME")},
                    };
                });
                telemetry.AddAspNetCoreInstrumentation();
                telemetry.AddGrpcClientInstrumentation();
                telemetry.AddHttpClientInstrumentation();
            });

        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseRouting();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapGrpcService<CartServiceImpl>();
                endpoints.MapGrpcService<HealthImpl>();

                // endpoints.MapGet("/", async context =>
                // {
                //     await context.Response.WriteAsync("Communication with gRPC endpoints must be made through a gRPC client. To learn how to create a client, visit: https://go.microsoft.com/fwlink/?linkid=2086909");
                // });
            });
        }
    }
}
