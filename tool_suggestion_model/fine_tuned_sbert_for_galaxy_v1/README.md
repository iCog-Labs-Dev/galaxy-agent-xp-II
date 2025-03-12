---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- generated_from_trainer
- dataset_size:73
- loss:CosineSimilarityLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: 'GFF-to-BED - converter - What it does


    This tool converts data from GFF format to BED format (scroll down for format
    description).


    Example


    The following data in GFF format:


    chr22  GeneA  enhancer  10000000  10001000  500      +   .  TGA

    chr22  GeneA  promoter  10010000  10010100  900      +   .  TGA


    Will be converted to BED (note that 1 is subtracted from the start coordinate):


    chr22   9999999  10001000   enhancer   0   +

    chr22  10009999  10010100   promoter   0   +


    About formats


    BED format

    Browser Extensible Data format was designed at UCSC for displaying data tracks
    in the Genome Browser. It has three required fields and several additional optional
    ones:


    The first three BED fields (required) are:


    1. chrom - The name of the chromosome (e.g. chr1, chrY_random).

    2. chromStart - The starting position in the chromosome. (The first base in a
    chromosome is numbered 0.)

    3. chromEnd - The ending position in the chromosome, plus 1 (i.e., a half-open
    interval).


    The additional BED fields (optional) are:


    4. name - The name of the BED line.

    5. score - A score between 0 and 1000.

    6. strand - Defines the strand - either ''+'' or ''-''.

    7. thickStart - The starting position where the feature is drawn thickly at the
    Genome Browser.

    8. thickEnd - The ending position where the feature is drawn thickly at the Genome
    Browser.

    9. reserved - This should always be set to zero.

    10. blockCount - The number of blocks (exons) in the BED line.

    11. blockSizes - A comma-separated list of the block sizes. The number of items
    in this list should correspond to blockCount.

    12. blockStarts - A comma-separated list of block starts. All of the blockStart
    positions should be calculated relative to chromStart. The number of items in
    this list should correspond to blockCount.

    13. expCount - The number of experiments.

    14. expIds - A comma-separated list of experiment ids. The number of items in
    this list should correspond to expCount.

    15. expScores - A comma-separated list of experiment scores. All of the expScores
    should be relative to expIds. The number of items in this list should correspond
    to expCount.


    GFF format

    General Feature Format is a format for describing genes and other features associated
    with DNA, RNA and Protein sequences. GFF lines have nine tab-separated fields:


    1. seqname - Must be a chromosome or scaffold.

    2. source - The program that generated this feature.

    3. feature - The name of this type of feature. Some examples of standard feature
    types are "CDS", "start_codon", "stop_codon", and "exon".

    4. start - The starting position of the feature in the sequence. The first base
    is numbered 1.

    5. end - The ending position of the feature (inclusive).

    6. score - A score between 0 and 1000. If there is no score value, enter ".".

    7. strand - Valid entries include ''+'', ''-'', or ''.'' (for don''t know/care).

    8. frame - If the feature is a coding exon, frame should be a number between 0-2
    that represents the reading frame of the first base. If the feature is not a coding
    exon, the value should be ''.''.

    9. group - All lines with the same group are linked together into a single item.

    '
  sentences:
  - 'MAF to BED - Converts a MAF formatted file to the BED format - This tool converts
    every MAF block to an interval line (in BED format) describing the position of
    that alignment block within a corresponding genome. /n Step 1 of 2: Choose multiple
    alignments from history to be converted to BED format. /n Step 2 of 2: Choose
    species from the alignment to be included in the output and specify how to deal
    with alignment blocks that lack one or more species. /n Choose species: The tool
    reads the alignment provided during Step 1 and generates a list of species contained
    within that alignment. Using checkboxes, you can specify taxa to be included in
    the output (only reference genome, shown in bold, is selected by default). If
    you select more than one species, then more than one history item will be created.
    /n Include/exclude blocks with missing species: If an alignment block does not
    contain any one of the species you selected and this option is set to exclude
    blocks with missing species, then coordinates of such a block will not be included
    in the output. /n Example 1: Include only reference genome (hg18 in this case)
    and include blocks with missing species. For the following alignment: s hg18.chr20
    56827368 75 + 62435964 GACAGGGTGCATCTGGGAGGG---... The tool will create a single
    history item: chr20 56827368 56827443 hg18_0 0 + chr20 56827443 56827480 hg18_1
    0 + /n Example 2: Include hg18 and mm8 and exclude blocks with missing species.
    For the following alignment: s hg18.chr20 56827368 75 + 62435964 GACAGGGTGCATCTGGGAGGG---...
    The tool will create two history items: History item 1 (for hg18): chr20 56827368
    56827443 hg18_0 0 + History item 2 (for mm8): chr2 173910832 173910893 mm8_0 0
    + /n MAF format: Multiple Alignment Format file. Stores multiple alignments at
    the DNA level between entire genomes. Each alignment ends with a blank line. Each
    sequence is on a single line. Lines starting with # are comments. Each alignment
    block starts with an ''a'' line followed by ''s'' lines for each sequence. /n
    BED format: Browser Extensible Data format used for displaying data in the UCSC
    Genome Browser. Required fields: 1. chrom - Chromosome name (e.g., chr1) 2. chromStart
    - Start position (0-based) 3. chromEnd - End position (exclusive). Optional fields:
    4. name - Name of the item 5. score - Score between 0 and 1000 6. strand - Either
    ''+'' or ''-'''
  - "Split MAF blocks - by Species - ### What It Does\n\nThe **Split MAF Block Species**\
    \ tool analyzes each block in a MAF (Multiple Alignment Format) file to identify\
    \ cases where a single block contains multiple sequences from the same species.\
    \ When this occurs, it splits the block into separate blocks, ensuring that each\
    \ block contains only one sequence per species.\n\nThe goal is to generate all\
    \ possible combinations of sequences where each species is represented exactly\
    \ once per block.\n\n### How It Works\n\n1. Scans each MAF block in the input\
    \ file.\n2. Detects if any species appears more than once in the block.\n3. Splits\
    \ the block into multiple new blocks.\n   - Each new block includes exactly one\
    \ sequence per species.\n   - All possible combinations of these sequences are\
    \ represented.\n4. Optionally, alignment columns that only contain gaps (\"empty\
    \ columns\") can be removed from the new blocks.\n\n### Example\n\n#### Original\
    \ MAF Block (containing multiple sequences for `hg18`):\n```\na score=5000\ns\
    \ hg18.chr1 100 50 + 247249719 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTAC\n\
    s hg18.chr2 500 50 + 243199373 TGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATG\n\
    s panTro2.chr1 150 50 + 228333871 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTA\n\
    ```\n\n#### Split into two new MAF blocks:\n```\na score=5000\ns hg18.chr1 100\
    \ 50 + 247249719 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTAC\ns panTro2.chr1\
    \ 150 50 + 228333871 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTA\n\na score=5000\n\
    s hg18.chr2 500 50 + 243199373 TGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATG\n\
    s panTro2.chr1 150 50 + 228333871 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTA\n\
    ```\n\n### Inputs\n\n- **MAF file to split**\n  - Select a MAF file containing\
    \ multiple alignments that you want to split by species.\n\n- **Collapse empty\
    \ alignment columns** (optional)\n  - If enabled, alignment columns that contain\
    \ only gaps in the new blocks will be removed, producing cleaner and more compact\
    \ alignments.\n\n### Output\n\n- A new MAF file where each block contains only\
    \ one sequence per species.\n- All possible combinations of unique species sequences\
    \ are represented as separate alignment blocks.\n\n### Use Cases\n\n- Preparing\
    \ MAF blocks for downstream analyses that require unique species representation\
    \ per block.\n- Simplifying complex MAF files with duplicate species entries.\n\
    - Removing unnecessary gaps from alignments by collapsing empty columns.\n\n###\
    \ Notes\n\n- The `collapse empty alignment columns` option is particularly useful\
    \ for eliminating columns that result from splitting blocks and no longer contain\
    \ meaningful data.\n- Header lines and scores are preserved in the new blocks.\n\
    - This tool can greatly increase the number of alignment blocks if there are many\
    \ combinations to represent."
  - 'Change Case - of selected columns - This tool breaks column assignments. To re-establish
    column assignments run the tool and click on the pencil icon in the resulting
    history item.

    The format of the resulting dataset from this tool is always tabular.


    What it does

    This tool selects specified columns from a dataset and converts the values of
    those columns to upper or lower case.

    Columns are specified as c1, c2, and so on.

    Columns can be specified in any order (e.g., c2,c1,c6).


    Example

    Changing columns 1 and 3 (delimited by Comma) to upper case in:

    apple,is,good

    windows,is,bad

    will result in:

    APPLE is GOOD

    WINDOWS is BAD'
- source_sentence: "Group - data by a column and perform aggregate operation on other\
    \ columns. - This tool allows you to **group** the input dataset by a particular\
    \ column and perform various **aggregate functions** on any specified column(s).\
    \ The available aggregate functions include **Mean**, **Median**, **Mode**, **Sum**,\
    \ **Max**, **Min**, **Count**, **Concatenate**, and **Randomly pick**.\n\n###\
    \ Key Functions:\n\n1. **Grouping**: \n   - The tool groups the dataset by the\
    \ values in a specified column. Once grouped, you can perform aggregate functions\
    \ on the columns of interest within each group.\n\n2. **Aggregate Functions**:\
    \ \n   - **Mean**: Computes the average value of the selected column within each\
    \ group.\n   - **Median**: Finds the middle value when the values are ordered\
    \ within each group.\n   - **Mode**: Identifies the most frequent value(s) within\
    \ each group. If multiple modes exist, all are reported.\n   - **Sum**: Adds up\
    \ the values in the specified column for each group.\n   - **Max**: Finds the\
    \ maximum value in the specified column within each group.\n   - **Min**: Finds\
    \ the minimum value in the specified column within each group.\n   - **Count**:\
    \ Counts the number of items in the specified column for each group.\n   - **Concatenate**:\
    \ Builds a comma-delimited list of values in the specified column for each group.\n\
    \   - **Concatenate Unique**: Builds a list of unique values, removing duplicates,\
    \ and joining them with commas.\n   - **Randomly Pick**: Picks a random value\
    \ from the specified column for each group.\n\n3. **Count and Count Unique**:\
    \ \n   - **Count** counts the total number of items in a specified column for\
    \ each group.\n   - **Count Unique** counts only the unique items in the specified\
    \ column for each group.\n\n4. **Concatenate vs Count**: \n   - **Concatenate**\
    \ and **Concatenate Unique** will return a comma-separated list of items for each\
    \ group, whereas **Count** and **Count Unique** return the count of items (either\
    \ total or unique).\n\n### Example Input:\n```\nchr22  1000  1003  TTT\nchr22\
    \  2000  2003  aaa\nchr10  2200  2203  TTT\nchr10  1200  1203  ttt\nchr22  1600\
    \  1603  AAA\n```\n\n### Example Grouping and Aggregation:\n\n1. **Grouping on\
    \ Column 4 while ignoring case** and performing **Count** on Column 1 will return:\n\
    ```\nAAA    2\nTTT    3\n```\n   - Here, `AAA` and `TTT` are grouped and counted\
    \ for occurrences.\n\n2. **Grouping on Column 4 while not ignoring case** and\
    \ performing **Count** on Column 1 will return:\n```\naaa    1\nAAA    1\nttt\
    \    1\nTTT    2\n```\n   - The case-sensitive grouping results in distinct counts\
    \ for `aaa`, `AAA`, `ttt`, and `TTT`.\n\n### Concatenate and Concatenate Unique:\
    \ \n   - **Concatenate**: Combines the values in the specified column for each\
    \ group, separated by commas.\n   - **Concatenate Unique**: Combines only unique\
    \ values in the specified column for each group.\n   - Example: If Column 1 contains\
    \ values `1, 1, 2, 3` for a group, the **Concatenate** function will return `1,\
    \ 1, 2, 3`, while **Concatenate Unique** will return `1, 2, 3`.\n\n### Tips: \n\
    1. **Handling Case Sensitivity**: \n   - The tool allows the option to **ignore\
    \ case** while performing operations like **Count** and **Concatenate**, which\
    \ can be helpful for grouping strings regardless of their case.\n\n2. **Multiple\
    \ Aggregate Functions**: \n   - You can apply multiple aggregate functions to\
    \ different columns within the same dataset. For example, you can calculate the\
    \ **Sum** for one column while finding the **Mean** for another.\n\n3. **Handling\
    \ Non-Numeric Data**: \n   - Functions like **Mean**, **Median**, **Sum**, **Max**,\
    \ and **Min** are typically used with numeric columns. Ensure your columns contain\
    \ the appropriate data types for accurate results.\n\n4. **Randomly Picking Values**:\
    \ \n   - The **Randomly pick** function allows for randomly selecting a value\
    \ from each group. This can be useful for sampling or testing purposes."
  sentences:
  - 'Filter collection -  - Synopsis

    Filters elements from a collection using a list supplied in a file.


    Description

    This tools allow filtering elements from a data collection. It takes an input
    collection and a text file with names (i.e. identifiers). The tool behavious is
    controlled by How should the elements to remove be determined? drop-down. It has
    the following options:


    Remove if identifiers are ABSENT from file

    Note how the tool deals with the Z entry.


    This tool will create new history datasets from your collection but your quota
    usage will not increase.'
  - "Extract Pairwise MAF blocks - given a set of genomic intervals - ### What it\
    \ does\n\nThis tool extracts pairwise alignment blocks from a MAF (Multiple Alignment\
    \ Format) file based on a set of genomic coordinates provided by the user. It\
    \ retrieves alignment blocks that overlap with specified intervals and trims them\
    \ to match the given coordinates when necessary.\n\n### How it works\n\n- **Input**:\n\
    \  1. A list of genomic intervals (typically in BED format or similar): each line\
    \ specifies a region by its chromosome, start, and end positions.\n  2. A MAF\
    \ file containing pairwise alignments.\n\n- **Output**:\n  - A new MAF file containing\
    \ only those alignment blocks that overlap the specified genomic intervals. Any\
    \ blocks that extend beyond the interval boundaries are trimmed accordingly.\n\
    \n### Key Features\n\n- **Precise trimming**: If an alignment block extends past\
    \ the START and/or END position of the interval, it is trimmed so that only the\
    \ relevant region is included.\n- **Multiple block retrieval**: A single genomic\
    \ interval may correspond to multiple MAF blocks. The tool retrieves and processes\
    \ all blocks that overlap with the interval.\n- **Support for pairwise alignments**:\
    \ This tool focuses on extracting blocks from pairwise MAF alignments available\
    \ on the Galaxy site.\n\n### Example\n\n#### Input genomic interval:\n```\nchr1\
    \   1000   2000\n```\n\n#### Superimposed on three MAF blocks:\n- **Block 1**\
    \ overlaps partially with the interval and is trimmed at the start.\n- **Block\
    \ 2** lies completely within the interval and is included in full.\n- **Block\
    \ 3** overlaps partially and is trimmed at the end.\n\n#### Output MAF blocks:\n\
    ```\nTrimmed Block 1 (starts at position 1000)\nFull Block 2\nTrimmed Block 3\
    \ (ends at position 2000)\n```\n\n### Common use cases\n\n- Extracting alignment\
    \ data for specific genomic regions of interest.\n- Preparing custom datasets\
    \ for focused comparative genomics analysis.\n- Reducing the size of MAF files\
    \ by including only relevant alignment blocks.\n\n### Tips\n\n- Ensure your input\
    \ intervals are correctly formatted and correspond to the reference genome used\
    \ in the MAF alignments.\n- This tool works with pairwise alignments and may not\
    \ be suitable for multi-species MAF files.\n- Trimmed blocks maintain the integrity\
    \ of alignment coordinates relevant to the input intervals.\n\n### Input Requirements\n\
    \n- Genomic intervals: Provide coordinates that specify the regions you want to\
    \ extract from the MAF file.\n- Pairwise MAF file: Ensure it matches the genome\
    \ assembly of your intervals and is formatted correctly."
  - 'Select - lines that match an expression - The select tool searches data for lines
    matching or not matching a given regular expression pattern. Special characters
    include ( ) { } [ ] . * ? + ^ $ which have specific meanings, such as matching
    the beginning (^), end ($), digits (\d), or whitespace (\s). Regular expressions
    allow for pattern matching with conditions like repetition ({n,m}) or alternation
    (|). Examples: ^chr([0-9A-Za-z])+ matches lines starting with chromosomes, (ACGT){1,5}
    matches 1 to 5 consecutive ''ACGT'', and (abc)|(def) matches either ''abc'' or
    ''def''. Comments can be matched using ^\W+#.'
- source_sentence: 'Change Case - of selected columns - This tool breaks column assignments.
    To re-establish column assignments run the tool and click on the pencil icon in
    the resulting history item.

    The format of the resulting dataset from this tool is always tabular.


    What it does

    This tool selects specified columns from a dataset and converts the values of
    those columns to upper or lower case.

    Columns are specified as c1, c2, and so on.

    Columns can be specified in any order (e.g., c2,c1,c6).


    Example

    Changing columns 1 and 3 (delimited by Comma) to upper case in:

    apple,is,good

    windows,is,bad

    will result in:

    APPLE is GOOD

    WINDOWS is BAD'
  sentences:
  - "Paste - two files side by side - This tool helps to merge two datasets side by\
    \ side while preserving the column assignments of the first dataset.\n\nWhat it\
    \ does\n1. **Functionality**\n   - Merges two datasets side by side.\n   - The\
    \ first (left) dataset’s column assignments (such as chromosome, start, end, and\
    \ strand) will be preserved.\n   - If needed, column assignments can be modified\
    \ by clicking the pencil icon in the history item.\n\n2. **Example**\n   - First\
    \ dataset:\n     a 1\n     a 2\n     a 3\n   - Second dataset:\n     20\n    \
    \ 30\n     40\n   - Pasting them together will produce:\n     a 1 20\n     a 2\
    \ 30\n     a 3 40"
  - "Stitch Gene blocks - given a set of coding exon intervals - ### What It Does\n\
    \nThe **Stitch Gene Block** tool reconstructs the complete coding sequences of\
    \ genes by stitching together multiple MAF alignment blocks that overlap the coding\
    \ exons of those genes.\n\nGenes typically consist of multiple coding exons, each\
    \ corresponding to separate genomic regions. These regions can be fragmented across\
    \ different MAF alignment blocks. This tool combines these fragments to produce\
    \ continuous, high-quality alignments for each gene.\n\n### How It Works\n\n1.\
    \ **Input** a list of gene intervals in **Gene BED format**, specifying the coding\
    \ regions (exons) for each gene.\n2. **Search** for all MAF blocks that overlap\
    \ these coding regions.\n3. **Sort** the overlapping MAF blocks by their alignment\
    \ score (higher scores first).\n4. **Stitch** the blocks together:\n   - Resolve\
    \ overlaps between blocks, prioritizing sequences from the block with the highest\
    \ alignment score.\n   - Concatenate blocks to form a continuous alignment covering\
    \ the entire coding sequence.\n5. **Output** the stitched alignments in **FASTA\
    \ format** for downstream analysis.\n\n### Example Workflow\n\n#### Inputs:\n\
    - **Gene intervals** (in Gene BED format):\n  - Example line: `chr1 1000 2000\
    \ Gene1`\n- **MAF alignment blocks** covering these regions.\n\n#### The tool\
    \ will:\n- Find all MAF blocks that overlap `chr1:1000-2000`.\n- Sort them by\
    \ score.\n- Resolve overlaps by picking the higher-scoring alignment.\n- Output\
    \ a stitched, continuous alignment of `Gene1` in FASTA format.\n\n### Inputs\n\
    \n- **Gene BED file**\n  - Contains intervals corresponding to coding regions\
    \ of genes.\n  - Example BED format:\n    ```\n    chrX 1000 1100 GeneA\n    chrX\
    \ 1500 1600 GeneA\n    ```\n\n- **MAF file**\n  - Multiple alignment format file\
    \ that contains alignment blocks overlapping the regions defined in the Gene BED\
    \ file.\n\n### Outputs\n\n- **FASTA alignments**\n  - One stitched alignment per\
    \ gene, spanning its coding regions.\n  - These alignments are suitable for downstream\
    \ evolutionary or functional analyses.\n\n### Use Cases\n\n- Constructing complete\
    \ coding sequence alignments for phylogenetic analysis.\n- Preparing alignments\
    \ for positive selection tests (e.g., dN/dS analyses).\n- Extracting high-confidence,\
    \ stitched alignments for gene regions across multiple species.\n\n### Notes\n\
    \n- Overlapping regions between blocks are resolved in favor of the block with\
    \ the highest alignment score to ensure quality.\n- If no MAF blocks overlap a\
    \ region, no alignment will be produced for that gene.\n- This tool outputs sequences\
    \ in FASTA format, not MAF format."
  - "Secure Hash / Message Digest - on a dataset - This tool helps to generate Secure\
    \ Hashes / Message Digests for a dataset using user-selected algorithms.\n\nWhat\
    \ it does\n1. **Functionality**\n   - Computes cryptographic hash values for datasets.\n\
    \   - Supports various hashing algorithms like MD5, SHA-1, SHA-256, etc.\n\n2.\
    \ **Usage**\n   - Select the dataset and choose the desired hashing algorithm.\n\
    \   - The tool will output the computed hash values.\n\n3. **Citation**\n   -\
    \ If you use this tool in Galaxy, please cite Blankenberg D, et al. In preparation."
- source_sentence: 'SFF converter -  - This tool extracts data from the 454 Sequencer
    SFF format and creates three files containing the: Sequences (FASTA), Qualities
    (QUAL) and Clippings (XML).'
  sentences:
  - 'g:Profiler - tools for functional profiling of gene lists - ### Dataset Formats


    The input dataset should be tabular with a column containing identifiers such
    as gene, protein, or microarray probe IDs. The output dataset is an HTML file
    with a link to the g:Profiler website.


    ### What It Does


    This tool generates a link to the **g:GOSt** tool (Gene Group Functional Profiling),
    which is part of the **g:Profiler** site from the University of Tartu, Estonia.
    g:GOSt retrieves the most significant **Gene Ontology (GO)** terms, **KEGG** and
    **REACTOME** pathways, and **TRANSFAC** motifs for a user-specified group of genes,
    proteins, or microarray probes. Additionally, g:GOSt supports the analysis of
    ranked or ordered gene lists, interactive visualization, and GO graph structure
    browsing.


    Multiple testing corrections are applied to extract only statistically significant
    results. The form for **g:GOSt** is pre-filled with IDs from the selected column
    of a tabular Galaxy dataset. Alternatively, genomic coordinates can be used (based
    on the latest Ensembl build), even if they correspond to SNPs rather than genes.
    g:GOSt will map SNPs to gene IDs.


    Once the tool finishes running, you can click the eye icon to follow the generated
    link. On the g:Profiler website, you can explore the g:GOSt results, adjust the
    form options, or use the provided links to run other g:Profiler tools using the
    same list of IDs.


    ### Features

    - Retrieve significant GO terms, KEGG, REACTOME pathways, and TRANSFAC motifs

    - Analyze ranked gene lists and SNPs (mapped to genes)

    - Interactive visualization of results

    - Multiple testing corrections to ensure statistical significance'
  - "Tag elements -  - Synopsis\nThis tool adds tags (including name: and group: tags)\
    \ to collection elements.\n\nDescription\n1. **Tagging Collection Elements**\n\
    \   - The relationship between element names and tags is specified in a two-column\
    \ tab-delimited file.\n   - If the file contains fewer entries than elements in\
    \ the collection, only matching list identifiers will be tagged.\n   \n2. **Creating\
    \ Name and Group Tags**\n   - To create `name:` or `group:` tags, prepend them\
    \ with `#`, `name:`, or `group:`.\n\n3. **More About Tags**\n   - **Simple Tags:**\
    \ Attach an alternative label to a dataset for easier retrieval.\n   - **Name\
    \ Tags:** Track dataset propagation through analyses—derived datasets inherit\
    \ the tag.\n   - **Group Tags:** Label groups of datasets (e.g., 'treatment' and\
    \ 'control' for differential expression analysis).\n\nThis tool enhances dataset\
    \ organization and facilitates structured analysis workflows in Galaxy."
  - "BED-to-bigBed - converter - This tool converts a sorted BED file into a bigBed\
    \ file.\n\nWhat it does\n1. **Functionality**\n   - Transforms a BED file into\
    \ the binary bigBed format for efficient storage and retrieval.\n   - Requires\
    \ the input BED file to be sorted.\n\n2. **Usage**\n   - Provide a sorted BED\
    \ file as input.\n   - The tool will generate a bigBed file as output.\n\n3. **Limitations**\n\
    \   - The `bedFields` option to specify non-standard fields is not supported.\n\
    \   - An AutoSQL file is required but is currently not supported in Galaxy."
- source_sentence: 'Convert genome coordinates - between assemblies and genomes -
    This tool converts genomic coordinates and annotations between different genome
    assemblies using the LiftOver utility from UCSC Genome Browser. It works with
    interval, GFF, and GTF datasets, converting them between genome assemblies, and
    produces two output files: one with mapped coordinates and the other with unmapped
    coordinates. The interval datasets should have chromosome in column 1, start coordinate
    in column 2, and end coordinate in column 3. BED comments and track lines will
    be ignored. This tool is useful for genome assembly liftover tasks and ensures
    annotation compatibility between assemblies. For example, converting hg16 intervals
    to hg18 intervals.'
  sentences:
  - 'Add column - to an existing dataset - This tool allows you to add a new column
    to your dataset by entering any value in the text box. The value will be appended
    to each row in the dataset. For example, if your original data looks like: chr1
    10 100 geneA, chr2 200 300 geneB, chr2 400 500 geneC, typing ''+'' in the text
    box will generate: chr1 10 100 geneA +, chr2 200 300 geneB +, chr2 400 500 geneC
    +. You can also add line numbers by selecting Iterate: YES. If you enter ''1''
    in the text box, it will add line numbers: chr1 10 100 geneA 1, chr2 200 300 geneB
    2, chr2 400 500 geneC 3.'
  - "Join two Datasets - side by side on a specified field - This tool allows you\
    \ to **join** two datasets based on a common field. It enables you to combine\
    \ the data from both datasets into a single dataset by matching values in a specified\
    \ column from each dataset. **Empty strings ('')** are not valid identifiers for\
    \ joining.\n\n### Key Features:\n\n1. **Common Field**: \n   - The tool joins\
    \ lines from two datasets where the values in the specified columns match.\n \
    \  - The columns are referenced by their number (e.g., 1st column, 2nd column,\
    \ etc.).\n\n2. **Joining Option**: \n   - You can choose to include only the matching\
    \ lines from both datasets, or you can keep all lines from the first dataset,\
    \ even if there is no match in the second dataset.\n\n3. **Invalid Identifiers**:\
    \ \n   - An empty string ('') cannot be used as a valid identifier for joining.\
    \ Ensure that the fields you are joining on contain meaningful, non-empty values.\n\
    \n### Example Datasets:\n**Dataset1:**\n```\nchr1  10  20  geneA\nchr1  50  80\
    \  geneB\nchr5  10  40  geneL\n```\n**Dataset2:**\n```\ngeneA  tumor-suppressor\n\
    geneB  Foxp2\ngeneC  Gnas1\ngeneE  INK4a\n```\n\n### Example 1: Joining on the\
    \ 4th column of Dataset1 and the 1st column of Dataset2\n\nJoining the 4th column\
    \ from Dataset1 (which contains gene identifiers) with the 1st column of Dataset2\
    \ (which also contains gene identifiers) results in:\n```\nchr1  10  20  geneA\
    \  geneA  tumor-suppressor\nchr1  50  80  geneB  geneB  Foxp2\n```\n\n### Example\
    \ 2: Including non-matching lines from Dataset1\n\nIf you choose to keep all lines\
    \ from Dataset1, even those that do not match any line in Dataset2, the result\
    \ will be:\n```\nchr1  10  20  geneA  geneA  tumor-suppressor\nchr1  50  80  geneB\
    \  geneB  Foxp2\nchr5  10  40  geneL\n```\n\n### Key Notes:\n\n- **Joining Columns**:\
    \ Ensure that the column you are using to join both datasets contains matching\
    \ values. The column numbers are used to refer to the fields in the datasets (e.g.,\
    \ 4 for the 4th column).\n- **Inclusion of Non-Matching Rows**: You can decide\
    \ whether to include rows from the first dataset even when no match is found in\
    \ the second dataset.\n- **Empty Identifiers**: If the field to join on contains\
    \ an empty string, it will be skipped, as empty strings are not valid identifiers.\n\
    \n### Tips:\n1. **Choosing the Correct Columns**: \n   - Double-check the columns\
    \ you are joining on. You should choose columns that contain common identifiers\
    \ or values that can meaningfully match across both datasets.\n\n2. **Handling\
    \ Non-Matching Data**: \n   - If you expect that not all rows will match, be sure\
    \ to choose the option to include rows from the first dataset that do not have\
    \ corresponding matches in the second dataset.\n\n3. **Data Quality**: \n   -\
    \ Ensure that the data in the columns you are joining on are clean and formatted\
    \ correctly. This ensures a successful join without issues like missing data or\
    \ unexpected results."
  - 'Nested Cross Product -  - Synopsis

    This tool organizes two dataset lists so that Galaxy''s normal collection processing
    produces an all-vs-all style analysis of the initial inputs when applied to the
    outputs of this tool.


    How to use this tool

    This tool can be used in and out of workflows. Workflows will be used to illustrate
    the ordering of tools and connections between them. Imagine a tool that compares
    two individual datasets and how that might be connected to list inputs in a workflow.


    The Dot Product of Two Collections

    In this configuration, datasets will be matched and compared element-wise. The
    first dataset of "Input List 1" will be compared to the first dataset in "Input
    List 2," and the resulting dataset will be the first dataset in the output list
    generated using this comparison tool. In this setup, the lists need to have the
    same number of elements and ideally matching element identifiers.


    Sometimes, however, the goal is to compare each element of the first list to every
    element of the second list. This tool enables that functionality.


    The Cartesian Product of Two Collections

    This tool consumes two flat lists (input_a and input_b). If input_a has length
    n and dataset elements identified as a1, a2, ... an, and input_b has length m
    with dataset elements identified as b1, b2, ... bm, this tool produces a pair
    of output nested lists (list:list collection type). The outer list has a length
    of n, and each inner list has a length of m, forming an n × m nested list.


    The first output is a nested list where the jth element inside the outer list''s
    ith element is a pseudo copy of the ith dataset of input_a. The second output
    is a nested list where the jth element inside the outer list''s ith element is
    a pseudo copy of the jth dataset of input_b.


    These nested structures ensure that when corresponding elements of the nested
    lists are matched, each combination of elements from input_a and input_b is compared
    once, producing a full cross-product comparison.'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/UKPLab/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 256, 'do_lower_case': False}) with Transformer model: BertModel 
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Convert genome coordinates - between assemblies and genomes - This tool converts genomic coordinates and annotations between different genome assemblies using the LiftOver utility from UCSC Genome Browser. It works with interval, GFF, and GTF datasets, converting them between genome assemblies, and produces two output files: one with mapped coordinates and the other with unmapped coordinates. The interval datasets should have chromosome in column 1, start coordinate in column 2, and end coordinate in column 3. BED comments and track lines will be ignored. This tool is useful for genome assembly liftover tasks and ensures annotation compatibility between assemblies. For example, converting hg16 intervals to hg18 intervals.',
    "Add column - to an existing dataset - This tool allows you to add a new column to your dataset by entering any value in the text box. The value will be appended to each row in the dataset. For example, if your original data looks like: chr1 10 100 geneA, chr2 200 300 geneB, chr2 400 500 geneC, typing '+' in the text box will generate: chr1 10 100 geneA +, chr2 200 300 geneB +, chr2 400 500 geneC +. You can also add line numbers by selecting Iterate: YES. If you enter '1' in the text box, it will add line numbers: chr1 10 100 geneA 1, chr2 200 300 geneB 2, chr2 400 500 geneC 3.",
    'Nested Cross Product -  - Synopsis\nThis tool organizes two dataset lists so that Galaxy\'s normal collection processing produces an all-vs-all style analysis of the initial inputs when applied to the outputs of this tool.\n\nHow to use this tool\nThis tool can be used in and out of workflows. Workflows will be used to illustrate the ordering of tools and connections between them. Imagine a tool that compares two individual datasets and how that might be connected to list inputs in a workflow.\n\nThe Dot Product of Two Collections\nIn this configuration, datasets will be matched and compared element-wise. The first dataset of "Input List 1" will be compared to the first dataset in "Input List 2," and the resulting dataset will be the first dataset in the output list generated using this comparison tool. In this setup, the lists need to have the same number of elements and ideally matching element identifiers.\n\nSometimes, however, the goal is to compare each element of the first list to every element of the second list. This tool enables that functionality.\n\nThe Cartesian Product of Two Collections\nThis tool consumes two flat lists (input_a and input_b). If input_a has length n and dataset elements identified as a1, a2, ... an, and input_b has length m with dataset elements identified as b1, b2, ... bm, this tool produces a pair of output nested lists (list:list collection type). The outer list has a length of n, and each inner list has a length of m, forming an n × m nested list.\n\nThe first output is a nested list where the jth element inside the outer list\'s ith element is a pseudo copy of the ith dataset of input_a. The second output is a nested list where the jth element inside the outer list\'s ith element is a pseudo copy of the jth dataset of input_b.\n\nThese nested structures ensure that when corresponding elements of the nested lists are matched, each combination of elements from input_a and input_b is compared once, producing a full cross-product comparison.',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities.shape)
# [3, 3]
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 73 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 73 samples:
  |         | sentence_0                                                                           | sentence_1                                                                           | label                                                         |
  |:--------|:-------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------|:--------------------------------------------------------------|
  | type    | string                                                                               | string                                                                               | float                                                         |
  | details | <ul><li>min: 10 tokens</li><li>mean: 204.86 tokens</li><li>max: 256 tokens</li></ul> | <ul><li>min: 10 tokens</li><li>mean: 205.71 tokens</li><li>max: 256 tokens</li></ul> | <ul><li>min: 1.0</li><li>mean: 1.0</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | sentence_1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | label            |
  |:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>Apply rules -  - Synopsis: This tool allows one to process an existing Galaxy dataset collection's metadata as tabular data, apply a series of rules to it, and generate a new collection.<br><br>Description: When used interactively in the tool form, a dynamic preview of the processing will be available in a tabular data viewer but this tool may be used in workflows as well where no such preview can be generated.<br><br>This tool is an advanced feature but has a lot of flexibility - it can be used to process collections with arbitrary nesting and can do many kinds of filtering, re-sorting, nesting, flattening, and arbitrary combinations thereof not possible with Galaxy's other, more simple collection operation tools.<br><br>More information about the rule processor in general can be found at our training site.<br><br>This tool will create new history datasets from your collection but your quota usage will not increase.</code>                                                                                                     | <code>Build list -  - Synopsis<br>Builds a new list collection from individual datasets or collections.<br><br>Description<br>This tool combines individual datasets or collections into a new collection. The simplest scenario is building a new collection from individual datasets (case A in the image below). You can merge a collection with individual dataset(s). In this case (see B in the image below), the individual dataset(s) will be merged with each element of the input collection to create a nested collection. Finally, two or more collections can be merged together creating a nested collection (case C in the image below).<br><br>Note: When merging collections (e.g., case C below), the input collection must have equal number of elements.</code>                                                                                                                                                                                                                                                                                                                            | <code>1.0</code> |
  | <code>Filter GTF data by attribute values_list -  - This tool filters a GTF (General Transfer Format) file based on a list of attribute values. The attribute values are taken from the first column of the GTF file, while the additional columns in the file are ignored during the filtering process. The primary use case for this tool is to filter a GTF file using a list of specific `transcript_ids`, `gene_ids`, or other attributes, such as those obtained from tools like Cuffdiff. This allows users to focus on specific genes or transcripts of interest.<br><br>### Key Functionality:<br><br>1. **Attribute-Based Filtering**: <br>   - The filtering condition is applied to the first column in the GTF file, which typically contains attribute values like `transcript_id` or `gene_id`. <br>   - Example: You may filter for entries that correspond to certain `transcript_ids` or `gene_ids`.<br><br>2. **File Format**: <br>   - GTF files are tab-delimited text files used to describe the structure of genes and transcripts. The first colu...</code> | <code>Join two Datasets - side by side on a specified field - This tool allows you to **join** two datasets based on a common field. It enables you to combine the data from both datasets into a single dataset by matching values in a specified column from each dataset. **Empty strings ('')** are not valid identifiers for joining.<br><br>### Key Features:<br><br>1. **Common Field**: <br>   - The tool joins lines from two datasets where the values in the specified columns match.<br>   - The columns are referenced by their number (e.g., 1st column, 2nd column, etc.).<br><br>2. **Joining Option**: <br>   - You can choose to include only the matching lines from both datasets, or you can keep all lines from the first dataset, even if there is no match in the second dataset.<br><br>3. **Invalid Identifiers**: <br>   - An empty string ('') cannot be used as a valid identifier for joining. Ensure that the fields you are joining on contain meaningful, non-empty values.<br><br>### Example Datasets:<br>**Dataset1:**<br>```<br>chr1  10  20  geneA<br>chr1  50...</code> | <code>1.0</code> |
  | <code>Filter empty datasets -  - Synopsis<br>Removes empty elements from a collection.<br><br>Description<br>This tool takes a dataset collection and filters out (removes) empty datasets. This is useful for continuing a multi-sample analysis when downstream tools require datasets to have content.<br><br>This tool will create new history datasets from your collection but your quota usage will not increase.</code>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | <code>Filter null elements -  - Synopsis<br>Removes null elements from a collection.<br><br>Description<br>This tool takes a dataset collection and filters out nulls. This is useful for removing elements that resulted from conditional execution of jobs.<br><br>This tool will create new history datasets from your collection but your quota usage will not increase.</code>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | <code>1.0</code> |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `num_train_epochs`: 1
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 8
- `per_device_eval_batch_size`: 8
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 1
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `use_ipex`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `dispatch_batches`: None
- `split_batches`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: False
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: False
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin

</details>

### Framework Versions
- Python: 3.12.8
- Sentence Transformers: 3.4.1
- Transformers: 4.49.0
- PyTorch: 2.6.0+cu124
- Accelerate: 1.4.0
- Datasets: 3.3.2
- Tokenizers: 0.21.0

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->