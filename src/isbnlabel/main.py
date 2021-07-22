import logging
import os.path
import sys
from argparse import ArgumentParser, REMAINDER
from typing import List

from barcode import ISBN13, EAN13
from barcode.writer import ImageWriter
from isbnlib import is_isbn10, to_isbn13, is_isbn13, canonical, meta
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages

logger = logging.getLogger(__name__)
logging.basicConfig()


def main(argv: List[str]) -> int:
    parser = ArgumentParser(description="Create ISBN-13 barcode images for a list of ISBNs")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-f", "--file", help="File containing ISBNs (one per line)")
    parser.add_argument("-O", "--outdir", default=".", help="Output directory")
    parser.add_argument("-o", "--outfile", default="labels.pdf", help="Output PDF file")
    parser.add_argument("-W", "--label-width", type=float, default=3.0, help="Label width (default: %(default)f)")
    parser.add_argument("-H", "--label-height", type=float, default=1.5, help="Label height (default: %(default)f)")
    parser.add_argument("isbns", nargs=REMAINDER, help="ISBNs to process")
    args = parser.parse_args(argv[1:])

    in_isbns = args.isbns
    if not in_isbns:
        in_isbns = []

    if args.file:
        with open(args.file, "r") as f:
            in_isbns.extend([line.strip() for line in f])

    isbns = []
    for isbn in set(in_isbns):
        if is_isbn10(isbn):
            isbn = to_isbn13(isbn)
        if not is_isbn13(isbn):
            logger.error("Not valid ISBN: %s" % isbn)
            continue
        isbns.append(canonical(isbn))

    outdir = os.path.realpath(args.outdir)
    if not os.path.isdir(outdir):
        os.makedirs(outdir, 0o755, exist_ok=True)

    sources = ["goob", "wiki", "openl"]

    images = {}
    for isbn in isbns:
        filename = os.path.join(outdir, isbn + ".png")
        if args.verbose:
            source = None
            metadata = None

            for source in sources:
                try:
                    metadata = meta(isbn, service=source)
                except Exception:
                    continue
                if metadata:
                    break

            print("Generate ISBN barcode at %s for %s (source %s)" % (filename, metadata, source))
        else:
            print("Generate ISBN barcode at %s for ISBN: %s" % (filename, isbn))

        with open(filename, "wb") as f:
            EAN13(isbn, writer=ImageWriter(format="PNG")).write(f)

        images[isbn] = filename

    filename = os.path.join(outdir, args.outfile)
    print("Generating PDF at: %s" % filename)
    print("Using labels of size %.2f\" x %.2f\"" % (args.label_width, args.label_height))

    pdf: PdfPages
    with PdfPages(filename) as pdf:
        for (isbn, image_filename) in sorted(images.items()):
            fig, ax = pyplot.subplots(figsize=(args.label_width, args.label_height))
            image = pyplot.imread(image_filename, format="png")
            im = ax.imshow(image)
            ax.axis('off')
            pdf.savefig(fig)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
