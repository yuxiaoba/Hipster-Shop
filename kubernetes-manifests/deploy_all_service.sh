#!/bin/bash

istioctl kube-inject -f adservice.yaml | kubectl apply -f -
istioctl kube-inject -f checkoutservice.yaml | kubectl apply -f -
istioctl kube-inject -f emailservice.yaml | kubectl apply -f -
istioctl kube-inject -f paymentservice.yaml  | kubectl apply -f -
istioctl kube-inject -f recommendationservice.yaml | kubectl apply -f -
istioctl kube-inject -f shippingservice.yaml | kubectl apply -f -
istioctl kube-inject -f cartservice.yaml | kubectl apply -f -
istioctl kube-inject -f currencyservice.yaml | kubectl apply -f -
istioctl kube-inject -f frontend.yaml | kubectl apply -f -
istioctl kube-inject -f productcatalogservice.yaml | kubectl apply -f -
istioctl kube-inject -f redis.yaml | kubectl apply -f -
