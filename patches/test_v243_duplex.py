from duplex import DuplexMode, Placement, map_backside, within_sheet


def close(a, b):
    return abs(a - b) < 1e-6


def assert_same(a, b):
    assert close(a.x, b.x)
    assert close(a.y, b.y)
    assert close(a.width, b.width)
    assert close(a.height, b.height)
    assert int(a.rotation) % 360 == int(b.rotation) % 360


def main():
    sheets = [(650.0, 450.0), (450.0, 650.0)]
    samples = [
        Placement(10, 20, 90, 54, 0),
        Placement(210, 120, 100, 70, 90),
        Placement(400, 300, 80, 100, 180),
    ]
    for sw, sh in sheets:
        for mode in DuplexMode:
            for p in samples:
                if not within_sheet(p, sw, sh):
                    continue
                back = map_backside(p, sw, sh, mode)
                assert within_sheet(back, sw, sh), (sw, sh, mode, p, back)
                front = map_backside(back, sw, sh, mode)
                # SELF_TURN changes rotation by 180 each pass, so two passes restore it.
                assert_same(front, p)

    p = Placement(10, 20, 90, 54, 0)
    lr = map_backside(p, 650, 450, DuplexMode.LEFT_RIGHT)
    assert close(lr.x, 550) and close(lr.y, 20)
    tb = map_backside(p, 650, 450, DuplexMode.TOP_BOTTOM)
    assert close(tb.x, 10) and close(tb.y, 376)
    le = map_backside(p, 650, 450, DuplexMode.LONG_EDGE)
    assert_same(le, tb)
    se = map_backside(p, 650, 450, DuplexMode.SHORT_EDGE)
    assert_same(se, lr)
    st = map_backside(p, 650, 450, DuplexMode.SELF_TURN)
    assert close(st.x, 550) and close(st.y, 376) and st.rotation == 180
    print('V2.4.3 duplex tests passed')


if __name__ == '__main__':
    main()
