PY ?= python3
.PHONY: demo eval test clean
demo:
	$(PY) -m pvagent run-all --approval approve --reviewer demo-reviewer
eval:
	$(PY) -m eval.run_eval
test:
	$(PY) -m unittest discover -s tests -t .
clean:
	rm -rf output
