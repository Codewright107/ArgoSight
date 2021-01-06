#!/usr/bin/env python3
"""Supplement module for 2021"""
import random
import datetime

class SupplementModule4857:
    def __init__(self):
        self.id = 4857
        self.ts = datetime.datetime.now()

    def run(self):
        return f"{self.id}"

if __name__ == "__main__":
    m = SupplementModule4857()
    print(m.run())
