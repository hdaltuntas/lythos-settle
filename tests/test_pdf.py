"""The PDF walker's layout rules: headings stay with their content, short tables stay whole."""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Table

from lythossettle import pdf


def story(html):
    return pdf.flowables(html, {}, pdf._styles(), A4[0] - 2 * pdf.MARGIN, A4[1] - 2 * pdf.MARGIN)


def table(rows):
    return ("<table width='100%'><tr><th>a</th><th>b</th></tr>"
            + "".join("<tr><td>1</td><td>2</td></tr>" for _ in range(rows)) + "</table>")


def test_a_heading_is_bound_to_the_table_after_it():
    s = story("<h2>Section</h2><h3>Sub</h3>" + table(3))
    group = s[0]
    assert isinstance(group, KeepTogether)
    kinds = [type(f) for f in group._content]
    assert kinds == [Paragraph, Paragraph, Table]


def test_keep_together_is_never_nested():
    # reportlab measures a nested KeepTogether as infinitely tall
    s = story("<h3>A</h3>" + table(3) + table(3) + "<p class='lead'><b>Caption</b></p>" + table(2))
    for f in s:
        if isinstance(f, KeepTogether):
            assert not any(isinstance(c, KeepTogether) for c in f._content)


def test_a_short_table_is_kept_whole_and_a_long_one_may_break():
    short, long_ = story(table(5)), story(table(pdf.SHORT_TABLE + 5))
    assert isinstance(short[0], KeepTogether)
    assert isinstance(long_[0], Table)


def test_a_page_break_comes_before_the_heading_it_belongs_to():
    s = story("<p>text</p><h2 style='page-break-before:always'>Next</h2>" + table(2))
    assert isinstance(s[1], PageBreak)
    assert isinstance(s[2], KeepTogether)
