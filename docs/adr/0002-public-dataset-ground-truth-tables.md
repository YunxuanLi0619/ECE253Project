# CER of public datasets goes in separate tables, not compared with the self-collected data

The ground truth of the self-collected data comes from `pdftotext` (see ADR-0001). The reference texts of public datasets come from different sources: SmartDoc-QA is human-transcribed; shadow sets such as RDD have no text, so the OCR result of the lossless image can only serve as pseudo ground truth. The three sources have different error characteristics, so each source gets its own table with the reference source stated in the header, and they are not averaged together. The pseudo-ground-truth table is interpreted only as relative improvement. All reference texts still pass through the same `normalize` of ADR-0001.

## Considered Options

- Merge into one overall table: simple to read, but mixes references of different trustworthiness; not adopted.
- Use only the self-collected data and no public sets: drops the public-dataset comparison the handout requires; not adopted.
