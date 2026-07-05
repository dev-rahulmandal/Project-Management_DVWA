"""
VulnForge scoring harness - SEPARATE from the deliberately-vulnerable target.

Nothing here is part of the two-origin app's surface. The app-side detectors
(later phases) only *write* solves via scoring.store; this package owns the
solve store and the read-only viewer. Keeping it out of api/ and web/ is what
lets the target stay a realistic, answer-key-free black-box.
"""
