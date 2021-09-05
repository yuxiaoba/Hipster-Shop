# Deploy kafka

## Install
```
$ kubectl create namespace kafka
$ kubectl apply -f operator.yaml  
$ kubectl get pod -n kafka --watch

$ kubectl apply -f local-storage.yaml
$ kubectl patch storageclass local-storage -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
$ kubectl apply -f kafka-local-pv.yaml
$ kubectl apply -f zookeeper-local-pv.yaml

$ kubectl apply -f kafka-persistent-single.yaml   -n kafka
$ kubectl get pod -n kafka --watch

$ kubectl get pod -n kafka 
NAME                                        READY   STATUS    RESTARTS   AGE
kafka-entity-operator-596648f765-zk6sl      3/3     Running   0          9m24s
kafka-kafka-0                               2/2     Running   0          9m56s
kafka-zookeeper-0                           1/1     Running   0          35m
strimzi-cluster-operator-7d6cd6bdf7-h2kc4   1/1     Running   0          37m

$ kubectl get svc -n kafka
  NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
  kafka-kafka-0                    NodePort    10.68.85.207    <none>        9094:39000/TCP               10m
  kafka-kafka-bootstrap            ClusterIP   10.68.117.188   <none>        9091/TCP                     10m
  kafka-kafka-brokers              ClusterIP   None            <none>        9091/TCP                     10m
  kafka-kafka-external-bootstrap   NodePort    10.68.227.215   <none>        9094:39092/TCP               10m
  kafka-zookeeper-client           ClusterIP   10.68.29.170    <none>        2181/TCP                     35m
  kafka-zookeeper-nodes            ClusterIP   None            <none>        2181/TCP,2888/TCP,3888/TCP   35m

// delete pv
kubectl patch  persistentvolume data-kafka-0   -p '{"metadata":{"finalizers":null}}'
kubectl patch  persistentvolume data-kafka-zookeeper-0   -p '{"metadata":{"finalizers":null}}'


```
