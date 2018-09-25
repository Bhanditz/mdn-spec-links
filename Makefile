GRIP=grip

all: SPECMAP.json

SPECMAP.json: browser-compat-data \
  ./browser-compat-data/add-specs.py \
  .browser-compat-data-process.py
	./browser-compat-data/add-specs.py
	./.browser-compat-data-process.py

index.html: README.md SPECMAP.json
	cp $< $<.tmp
	echo >> $<.tmp
	echo "## Spec JSON files" >> $<.tmp
	echo >> $<.tmp
	for file in *.json; do \
	    if [[ "$$file" != "MDNCOMP-DATA.json" ]]; then \
	        echo "* [$$file]($$file)" >> $<.tmp; \
	    fi; \
	done
	$(GRIP) --title=$< --export $<.tmp - > $@
	$(RM) $<.tmp
