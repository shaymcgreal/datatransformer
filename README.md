# CSV Account Analysis & Duplicate Detection

A WIP Python tool for analyzing CSV data files, validating data quality, and detecting duplicate records using advanced fuzzy matching algorithms.

## Features

- **Data Quality Scoring**: Validates fields based on content rules and assigns weighted scores
- **Advanced Duplicate Detection**: Uses multiple blocking strategies and weighted fuzzy matching
- **Phonetic Matching**: Employs Double Metaphone algorithm for name-based blocking
- **Configurable Thresholds**: Adjustable similarity thresholds for duplicate detection
- **Progress Tracking**: Visual progress bars during processing of large datasets
- **Comprehensive Output**: Detailed scoring and matching information in the output CSV

## Installation

1. Clone the repository
2. Install required dependencies:

```bash
pip install rapidfuzz Metaphone tqdm
```

## Usage

Basic usage:

```bash
python accountBlankCheck0.8.py input_file.csv
```

Advanced options:

```bash
python accountBlankCheck0.8.py input_file.csv -o output_file.csv --debug --graph
```

### Command Line Arguments

- `input_file`: Path to the input CSV file (required)
- `-o, --output_file`: Path for the output CSV file (optional)
- `--debug`: Enable debug mode for detailed processing information
- `--graph`: Generate visualization of the analysis results (planned feature)

## Configuration

The script includes several configurable parameters at the top of the file:

- `SPECIAL_SCORING_GUIDE`: Field importance grades (a=critical, b=important, c=standard)
- `GRADE_WEIGHTS`: Scoring weights for different importance grades
- `DUPLICATE_FIELD_WEIGHTS`: Weight distribution for fields in duplicate matching
- `BLOCKING_FIELDS`: Fields used for initial candidate selection
- `SIMILARITY_THRESHOLD`: Minimum score to consider records as duplicates (0-100)

## How It Works

1. **Field Scoring**: Analyzes each field's data quality using field-specific rules
2. **Record Blocking**: Groups similar records using phonetic algorithms and field normalization
3. **Similarity Calculation**: Compares potentially matching records using weighted fuzzy matching
4. **Output Generation**: Creates a new CSV with all original data plus quality and matching information

### Output Columns

The output CSV contains the original data plus additional columns:

- `*_score`: Individual field scores
- `total_row_score`: Sum of all field scores
- `final_status`: Pass/Fail based on critical field requirements
- `duplicate_score`: Similarity score with best match (if above threshold)
- `duplicate_match_details`: Details about the matched record
- `is_matched_to`: Information when other records match to this one
- `is_duplicate_or_matched`: Boolean flag for quick filtering
- `match_key`: Numeric key linking all records in a match group

## Development

### Code Structure

- Field scoring in `get_field_score()`
- Value normalization in `normalize_value()`
- Main processing logic in `process_csv()`

### Adding New Features

1. **New Field Types**: Extend `normalize_value()` and `get_field_score()` with additional field type handling
2. **Additional Algorithms**: Consider adding alternative matching algorithms in a pluggable way
3. **Visualization**: Implement the `create_visualizations()` function to add reporting capabilities

## License

This project is licensed under the MIT License - see the LICENSE file for details.

The MIT License is a permissive software license that:
- Allows users to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software
- Only requires the original copyright notice and license notice to be included in all copies
- Provides the software "as is" without warranties
- Does not restrict commercial use
- Does not hold the author liable for any issues with the software

To apply this license officially, create a LICENSE file in your repository.

## Deployment

To deploy this project to your GitHub repository:

1. **Initialize Git Repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Connect to GitHub Repository**:
   ```bash
   git remote add origin https://github.com/shaymcgreal/datatransformer.git
   ```

3. **Push to GitHub**:
   ```bash
   git push -u origin main
   ```

4. **Update Existing Repository**:
   ```bash
   git add .
   git commit -m "Update with new features"
   git push
   ```

5. **Create Release** (Optional):
   - Go to your GitHub repository
   - Click on "Releases"
   - Create a new release with a version tag
   - Add release notes

### CI/CD Integration

To set up automated testing and deployment:
1. Create a `.github/workflows` directory
2. Add a workflow file (e.g., `test.yml`) for automated testing
3. Configure deployment actions as needed

## Acknowledgments

- Uses [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) for fuzzy string matching
- Employs [Metaphone](https://pypi.org/project/Metaphone/) for phonetic algorithms
- Utilizes [tqdm](https://github.com/tqdm/tqdm) for progress visualization
