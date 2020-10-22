FROM registry.cn-shenzhen.aliyuncs.com/yuxiaoba/k6:base
MAINTAINER yuxiaoba

USER root
COPY --chown=root:root ./loadgenerator.js /loadgenerator

WORKDIR /loadgenerator
ENTRYPOINT ["k6","run", "/loadgenerator/loadgenerator.js", "-u", "10", "-d", "24h", "-o", "influxdb=http://monitoring-influxdb.default:8086"]