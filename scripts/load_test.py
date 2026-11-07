"""Chat-with-a-book load test for any OpenAI-compatible server. Measures TTFT."""
import argparse, asyncio, json, pathlib, random, statistics, time
from openai import AsyncOpenAI

INSTRUCTIONS = ("You are a reading assistant. Answer the reader's question using only "
                "the passage below. Keep answers short.\n\nPASSAGE:\n")

async def one_request(client, args, books, question, results):
    book = random.choice(books)            # which book this reader is asking about
    start = time.perf_counter()
    first = None
    tokens = 0
    try:
        # with_raw_response lets us read HTTP headers (needed in Lab 2)
        raw = await client.chat.completions.with_raw_response.create(
            model=args.model,
            messages=[{"role": "system", "content": INSTRUCTIONS + book},
                      {"role": "user", "content": question}],
            max_tokens=200,
            stream=True,
            # Qwen3 "thinks" before answering by default; turn it off
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        served_by = {k: v for k, v in raw.headers.items() if k.startswith("x-litellm-model")}
        async for chunk in raw.parse():
            if chunk.choices and chunk.choices[0].delta.content:
                if first is None:
                    first = time.perf_counter()
                tokens += 1
        results.append({"ok": True, "ttft": first - start if first else None,
                        "total": time.perf_counter() - start, "tokens": tokens,
                        "served_by": served_by})
    except Exception as e:
        results.append({"ok": False, "error": str(e)[:200]})

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://localhost:8000/v1")
    p.add_argument("--api-key", default="none")
    p.add_argument("--model", default="Qwen/Qwen3-8B")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--books", type=int, default=1, help="how many different books to ask about")
    p.add_argument("--repeat", type=int, default=1, help="send the question list this many times")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    client = AsyncOpenAI(base_url=args.base_url, api_key=args.api_key)
    books = [f.read_text() for f in sorted(pathlib.Path("data/books").glob("*.txt"))][:args.books]
    questions = [q.strip() for q in open("data/questions.txt") if q.strip()] * args.repeat

    sem = asyncio.Semaphore(args.concurrency)   # at most N requests in flight
    results = []
    async def limited(q):
        async with sem:
            await one_request(client, args, books, q, results)

    t0 = time.perf_counter()
    await asyncio.gather(*(limited(q) for q in questions))
    wall = time.perf_counter() - t0

    ok = [r for r in results if r["ok"] and r["ttft"]]
    ttfts = sorted(r["ttft"] for r in ok)
    print(f"books: {len(books)}  requests ok/failed: {len(ok)}/{len(results) - len(ok)}")
    if ttfts:
        print(f"TTFT median: {statistics.median(ttfts)*1000:.0f} ms")
        print(f"TTFT p90:    {ttfts[int(len(ttfts)*0.9) - 1]*1000:.0f} ms")
        print(f"output tokens/s (total): {sum(r['tokens'] for r in ok) / wall:.0f}")
    if args.out:
        json.dump(results, open(args.out, "w"), indent=1)

asyncio.run(main())
