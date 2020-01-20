#!/usr/bin/env python3
"""Supplement module for 2020"""
import random
import datetime

class SupplementModule3908:
    def __init__(self):
        self.id = 3908
        self.ts = datetime.datetime.now()

    def run(self):
        return f"{self.id}"

if __name__ == "__main__":
    m = SupplementModule3908()
    print(m.run())
