"""Lossless compact SVG syntax for the largest historical vector drawings."""
from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path


def compact(svg):
    def number(value):
        return str(int(value)) if value == int(value) else str(value)

    def command(letter, points):
        return letter + ' '.join(number(v) for point in points for v in point)

    class Pen(BasePen):
        def __init__(self):
            super().__init__(None)
            self.parts = []
            self.current = (0, 0)
            self.start = (0, 0)

        def _moveTo(self, p):
            self.parts.append(command('M', [p]))
            self.current = self.start = p

        def _lineTo(self, p):
            x, y = self.current
            choices = [command('L', [p])]
            if (p[0]-x)+x == p[0] and (p[1]-y)+y == p[1]:
                choices.append(command('l', [(p[0]-x, p[1]-y)]))
            if p[0] == x:
                choices.append('V' + number(p[1]))
                if (p[1]-y)+y == p[1]: choices.append('v' + number(p[1]-y))
            if p[1] == y:
                choices.append('H' + number(p[0]))
                if (p[0]-x)+x == p[0]: choices.append('h' + number(p[0]-x))
            self.parts.append(min(choices, key=len))
            self.current = p

        def _curveToOne(self, a, b, c):
            x, y = self.current
            absolute = command('C', [a, b, c])
            relative = command('c', [(p[0]-x, p[1]-y) for p in (a, b, c)])
            # Only use relative floats when subtraction is exactly reversible.
            exact = all((p[0]-x)+x == p[0] and (p[1]-y)+y == p[1] for p in (a, b, c))
            self.parts.append(min([absolute, relative], key=len) if exact else absolute)
            self.current = c

        def _closePath(self):
            self.parts.append('Z')
            self.current = self.start

        def _endPath(self):
            pass

    pen = Pen()
    parse_path(svg, pen)
    return ''.join(pen.parts)
