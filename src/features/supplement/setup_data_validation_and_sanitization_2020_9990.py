#!/usr/bin/env python3
"""Supplement module for 2020"""
import random
import datetime

class SupplementModule9990:
    def __init__(self):
        self.id = 9990
        self.ts = datetime.datetime.now()

    def run(self):
        return f"{self.id}"

if __name__ == "__main__":
    m = SupplementModule9990()
    print(m.run())
