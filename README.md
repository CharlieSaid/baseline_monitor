# Baseline Monitor
 - By Charlie Said

A leaderboard of the best HYSA rates, updated daily.

<https://charliesaid.github.io/baseline_monitor/>

TODO: Add screenshot of page here.

![Update Rates](https://github.com/CharlieSaid/baseline_monitor/actions/workflows/update-rates.yml/badge.svg)

***

## Why
I want to compare HYSA rates, and I don't like using [NerdWallet](https://www.nerdwallet.com/banking/m/standout-high-yield-savings-products) or watching a YouTube video on "the best HYSAs in 2026!".  This website is a simple, stable dashboard showing HYSA rates, updated automatically via GitHub Action, for long-term monitoring of HYSAs.

One thing that is often left out of HYSA comparisons are [T-Bill ladders](https://www.sofi.com/learn/content/guide-treasury-ladders/) and [money market funds](https://investor.vanguard.com/investment-products/money-markets).  I've included those in this comparison as well.

## Who this is for
Ultimately, I made this for me, because I like knowing what rate my cash is earning and could be earning at a different bank.  This project is for anyone with that same inclination.

In more academic terms, providing price transparency for all buyers in a free market increases the competition incentive for sellers.  Millions of Americans overpay for products which underdeliver relative to competing products, simply because they aren't aware of the cheaper, better alternatives.  The more simple, clear comparison we can have between market products, the better those products will become.

## How it works
 - GitHub Actions runs `fetch_rates.py`, which triggers all 24 Python web scrapers.
 - Results get written to `data/rates.json` and `data/history.json`.
 - The webpage is static and loads the data from GitHub.

Since the data is so basic and takes minimal space, I didn't feel a need to use a dedicated database; this architecture is lightweight and simple, appropriate for the scale of this project.

## How to run locally
`python3 fetch_rates.py`, using Python 3.12+.

## Tech Stack
 - Python stdlib
 - HTML/CSS/JS
 - GitHub Actions
 - GitHub Pages

## Disclaimers
 - This is not financial advice.
 - You are unique and special and should make your own decisions.
 - This project is just providing information.
 - Repo has MIT license.