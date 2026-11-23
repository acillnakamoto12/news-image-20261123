# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/acillnakamoto12/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/acillnakamoto12/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One image summing up the world's news of Monday, 23 November 2026: the tanker war escalating in the Strait of Hormuz, NATO meeting over Russian missiles in Poland, Asian markets reeling on AI fears, Zelenskyy urging the US to send Patriot missiles, the Ebola fight at risk in Congo, and a father and daughter detained by ICE at Seattle airport. The date it sums up is printed on the image itself.

## How it was made

`generate.py` (Python 3 + Pillow, no network) paints `entry.png` (1024×1024) from `news.json` — six stories verified against AP, Reuters, Al Jazeera and The Hindu reporting of 23 November 2026, laid out as a newspaper front page: a masthead with the date, one lead story, and five more across regions and fields. The layout is measured before it is drawn, so the text can never overflow the page. `main.ts` (Node, standard library only) checks the image is a real 1024×1024 PNG and copies it to the output directory; it writes the same bytes on every run.

## Run it

```sh
python3 generate.py
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=8w050qy5&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
