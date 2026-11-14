# Review packet 1 — errata (recorded before the verdict was read)

The feature hash table embedded in `review-prompt-1.md` was computed before two subsequent edits:

1. M2 scenario ids were renumbered from `SCN-1001…` to `SCN-2001…` because AI-06 already used the
   earlier range. The uniqueness check in GT-02 caught the collision.
2. Feature header comments were updated to state that the files execute from M2 onward.

Behavioral scenario wording is unchanged except for the identifier renumbering. Current hashes:

| `docs/stories/DT-05.feature` | `f348df16d5bb28945e6a16bbab116fb40cf5f6cb2ceeb69fe26ef2c4b36ece20` |
| `docs/stories/DT-06.feature` | `8b6630b2408e5ced946ec69fc97a014c45fcdf5e3c31eeb9a8603f007de703cd` |
| `docs/stories/AS-02.feature` | `4ea37ca50432b92113e4272826d7b75555677aaf3ff01cb91a46b1d4c29ede78` |
| `docs/stories/AS-03.feature` | `320cfdc2e32625e9dc4b6da11d6f1594e227eb3971ff17f8974d963b30ed00ee` |
| `docs/stories/AS-05.feature` | `2172b7f437f682753df4479b4329e8e73f7d267dc2776b2a7473c207116ac797` |
| `docs/stories/GT-01.feature` | `b7c5abe0dbe3120169355dbfde3e44b6a989a87471f24862157060f1e77afa07` |
| `docs/stories/GT-02.feature` | `7706223c5355fccbe3b05c37494b0ea48c2beda3bec0db07367a5d4f3d73af69` |
| `docs/stories/GT-03.feature` | `f81b51c4891e4a98da7bf02956ca9fc1a376f46df0ac4325f925d0a14432a85d` |
| `docs/stories/PG-01.feature` | `c32e182565f3fb279c2ff482fbfb0749d98c96b86f60c9e2ea575d6a13ec3e15` |
| `docs/stories/DT-01.feature` | `7c597f70673654a0e048ec923cc04073b9b424fd7c54b7254b635b4936b3b5e8` |
| `docs/stories/DT-02.feature` | `4e9ff5c1891763ea4160ab4bf7b55a86ddacdf0a7765cfa6dcd5b7694ffc3774` |
| `docs/stories/DT-03.feature` | `4c581fc95949e64ece04bfacadb6aa59a61358921ca58c2a9159aad0a1a193dc` |
| `docs/stories/DT-04.feature` | `3d525a0a7bdb2dbfc8a555e3e57e88a28f5574667b6f043b2903361d1c68d64a` |
| `docs/stories/AS-01.feature` | `bb214629f16293b719ce42a23a67ee21735163d5f1ad13861507086cdf6592b2` |
| `docs/stories/FT-01.feature` | `d58eeec05ce2072b81fd656531369ae2d329a9fcc09975688d2750fc044c217a` |
| `docs/stories/FT-02.feature` | `bdf55dafaa3fa498242c5fd5d3e27961281679ea612766dce207542cb7cacae8` |
| `docs/stories/AI-01.feature` | `381663033f88f4915481f292c912e94041774497aa74d22bb41a34b17276ef67` |

The reviewer sees the working tree, so these are the authoritative hashes for this submission.
