"""Download 20 public-domain books and save a ~5,000-token passage from each."""
import pathlib, urllib.request

BOOKS = {  # name: Project Gutenberg ID
    "pride_and_prejudice": 1342, "frankenstein": 84, "sherlock_holmes": 1661,
    "moby_dick": 2701, "dracula": 345, "alice_in_wonderland": 11,
    "tale_of_two_cities": 98, "tom_sawyer": 74, "huckleberry_finn": 76,
    "jane_eyre": 1260, "wuthering_heights": 768, "dorian_gray": 174,
    "great_gatsby": 64317, "great_expectations": 1400, "emma": 158,
    "jekyll_and_hyde": 43, "war_of_the_worlds": 36, "treasure_island": 120,
    "metamorphosis": 5200, "war_and_peace": 2600,
}

out = pathlib.Path("data/books")
out.mkdir(parents=True, exist_ok=True)
for name, gid in BOOKS.items():
    url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
    text = urllib.request.urlopen(url).read().decode("utf-8", errors="ignore")
    passage = text[30_000:50_000]   # skip the front matter; ~20,000 characters ≈ 5,000 tokens
    (out / f"{name}.txt").write_text(passage)
    print(f"saved {name}: {len(passage):,} characters")
