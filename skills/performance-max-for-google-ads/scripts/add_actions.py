#!/usr/bin/env python3
"""Add your recommended fixes to the review, after checking each one.

Reads OUTPUT/pmax-review.json from audit.py and an actions file you wrote,
refuses any action that points at no finding, has no Official or
Practitioner rule label, or would cut a channel on its average cost per
conversion, then rewrites the workbook and the summary with the fixes in.

    python3 scripts/add_actions.py --out OUTPUT --actions actions.json

OUTPUT/actions.json:
    {"actions": [{"finding": "F3", "kind": "fix", "action": "Add brand exclusions for ...",
                  "where": "Campaign settings, Brand exclusions", "label": "Official", "priority": 1}],
     "negatives": [{"search": "plumber jobs denver", "campaign": "PMax | Leads", "reason": "Job seekers"}]}

label is Official, Practitioner rule, or Both when each sentence starts with its own label.
Each negative is checked against the search terms report: it must be there, must not have
converted and must not be a brand search. It is written as an exact match negative to review.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import outputs  # noqa: E402
import pmax_write as write  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="the folder audit.py wrote to")
    parser.add_argument("--actions", required=True, help="your actions file")
    args = parser.parse_args()

    review_path = os.path.join(args.out, "pmax-review.json")
    if not os.path.isfile(review_path):
        raise SystemExit("Run audit.py first. I can't find %s." % review_path)
    if not os.path.isfile(args.actions):
        raise SystemExit("I can't find the actions file %s." % args.actions)
    try:
        with open(args.actions, encoding="utf-8") as handle:
            given = json.load(handle)
    except ValueError as err:
        raise SystemExit("The actions file is not valid JSON: %s." % err)
    review = outputs.read_json(review_path)
    if not isinstance(given, dict):
        given = {"actions": given}
    actions = write.validate_actions(review, given.get("actions", []))
    negatives = write.validate_negatives(review, given.get("negatives", []))
    if not actions and not negatives:
        raise SystemExit('The actions file has no actions and no negatives. Add at least one under "actions" or "negatives".')
    text = write.write_all(review, args.out, actions, negatives)
    print(text)
    print("Added %d actions and %d negatives to review. Wrote the files to %s" % (len(actions), len(negatives), args.out))


if __name__ == "__main__":
    main()
