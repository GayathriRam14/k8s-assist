.PHONY: install agent cluster destroy bootstrap

agent:
	pip install -e .

cluster:
	kind create cluster --name kubectlai-demo-cluster

destroy:
	kind delete cluster --name kubectlai-demo-cluster

bootstrap:
	kubectl apply -f manifests/
	kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
	kubectl patch deployment metrics-server -n kube-system \
		--type='json' \
		-p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'