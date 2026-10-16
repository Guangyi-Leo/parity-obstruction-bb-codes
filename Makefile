# Reproduction targets.  Override the interpreter with
#   make PY=/path/to/python test
#
# The solver runs that produced data/ and the DRAT proofs are NOT re-run here:
# they take days.  These targets rebuild everything derived from those outputs
# and re-check it.
PY ?= python3
export PYTHONPATH := $(CURDIR):$(CURDIR)/figures/src:$(CURDIR)/figures:$(PYTHONPATH)

.PHONY: all test tables figures check revision verify-proofs clean

all: test check

# the test suite: lemma checks, template pullbacks, the two mod-4 identities
# and the twisted coset identity (sampled, so it runs in about a minute)
test:
	$(PY) -m tests.test_small
	$(PY) -m tests.test_template_pullback
	$(PY) -m tests.test_mod4_general
	$(PY) -m tests.test_mod4_identity
	$(PY) -m tests.test_twisted_identity --sample 25

tables:
	$(PY) -m twoblock.make_tables

# rebuild every table and figure, the manuscript, and every check (minutes)
figures check:
	bash run.sh

# also re-run the revision's verification scripts (adds ~5 min; --revision-slow
# adds the q = 32 key enumeration and the forced-involution runs, ~35 min)
revision:
	bash run.sh --revision

# re-check the DRAT proofs.  With the Zenodo archive unpacked over certs/ this
# checks the proofs themselves; without it, each refutation is re-run from the
# shipped CNF and the fresh proof is checked instead.  See README.md.
verify-proofs:
	bash verify_proofs.sh

clean:
	rm -rf figures/*.png figures/*.pdf tables/*.tex build_tex dist revision/work
