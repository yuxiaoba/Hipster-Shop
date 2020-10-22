FROM golang:1.14.7 AS builder
WORKDIR /build/src
ENV GOPROXY https://goproxy.cn
COPY . .
RUN go build -gcflags='-N -l' -tags netgo -o /checkoutservice .

FROM alpine as release
RUN apk add --no-cache ca-certificates procps
RUN GRPC_HEALTH_PROBE_VERSION=v0.2.0 && \
    wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
    chmod +x /bin/grpc_health_probe
COPY --from=builder /checkoutservice /checkoutservice
EXPOSE 5050
ENTRYPOINT ["/checkoutservice"]
