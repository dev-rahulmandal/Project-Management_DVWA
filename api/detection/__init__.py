"""
Passive solve-detection (Phase 2) - server-side, invisible to a black-box tester.

An after-handler middleware inspects the request+response for the SUCCESS
signature of each vuln and records a solve to the SEPARATE scoring store. It
never alters a response and never runs for non-detector routes. Gated by
config.VF_SCORING. This code is white-box visible (open repo) but leaves zero
trace in the running target's observable behaviour.
"""
