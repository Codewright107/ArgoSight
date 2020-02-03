#!/usr/bin/env python3
"""Supplement module for 2020"""
import random
import datetime

class SupplementModule1925:
    def __init__(self):
        self.id = 1925
        self.ts = datetime.datetime.now()

    def run(self):
        return f"{self.id}"

if __name__ == "__main__":
    m = SupplementModule1925()
    print(m.run())
