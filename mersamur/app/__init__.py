"""Product code for the fragility checker.

Only `sectors_client` (not yet written) may touch the network. Everything in this
package reads cached payloads, which is what lets the daily cycle run for free.
"""
