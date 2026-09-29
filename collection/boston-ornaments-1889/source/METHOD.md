# Boston Ornaments 1889

Original JP2 leaves from the 1889 Boston specimen are retained unchanged. Acquisition URLs, archive members and hashes are in reference/acquisition.json. The requested Boston survey is tracked centrally in ../../boston-cuts-1889/source/inventory.json.

Individual word ornaments and border components are isolated from catalogue numbers, prices and sample text. Repeated compositions demonstrate the same parts and are retained on full source pages. Native crop coordinates, explicit erase rectangles and all preparation settings are in tracing.json. PUA assignments are stable within this font family; icon IDs are globally unique.

Potrace 1.16 fits cubic curves after optional local paper correction: a 25-pixel maximum filter and radius-4 Gaussian estimate paper illumination; each native gray value is divided by that estimate. This does not add strokes or close gaps. Three thresholds make nested masks; exact PathOps differences create disjoint primary, secondary and tertiary regions. Opacities are 1, 0.55 and 0.25. These tones are modern interpretations of the scanned impressions.

Uniform scaling retains source aspect ratios, fits the longest ink dimension within 1800 units of the 2048-unit em, and centres short ornaments vertically. Sidebearings are 64 units. Paper and neighbouring labels are removed only with recorded crop boundaries or explicit rectangles. No pictorial content is invented. Normal builds use the committed CFF TTX master and do not need Potrace or the network.

Prepare with scripts/trace_specimen.py boston-ornaments-1889 --jobs 4 --cache workspace/boston-expansion/trace-cache, then import and build through scripts/fontrevival.py.

The 715 exports cover printed pp. 258–270. Complete frames and separable printing components retain their distinct uses. Connected repeats that cannot be isolated without slicing artwork are recorded in inventory.json and preserved in the complete frame. Recorded threshold overrides preserve thin K-series curls, fine corner lines and engraved counters. The repeated publisher emblem is exported once from p. 258.
