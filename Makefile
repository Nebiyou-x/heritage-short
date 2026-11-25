.PHONY: film validate clean

validate:
	python -m pipeline.validate storyboard.json schema/storyboard.schema.json

film: validate
	python -m pipeline.run storyboard.json

clean:
	rm -rf outputs/final_* outputs/temp_*