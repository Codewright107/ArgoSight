#!/usr/bin/env python3
"""Supplement module for 2021"""
import random
import datetime

class SupplementModule3221:
    def __init__(self):
        self.id = 3221
        self.ts = datetime.datetime.now()

    def run(self):
        return f"{self.id}"

if __name__ == "__main__":
    m = SupplementModule3221()
    print(m.run())
