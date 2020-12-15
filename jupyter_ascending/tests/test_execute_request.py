from jupyter_ascending.requests.execute import _find_cell_number


def test_find_cell_number():
    assert (
        _find_cell_number(
            [
                "\n",
                "# %%\n",
                "print('hello')\n",
                "print('wow!')",
                "# %%\n" "TARGET = True",
                "\n",
                "# %%",
                "# Too Far",
                "# Still too far",
            ],
            5,
        )
        == 1
    )


def test_find_cell_number_with_more_spaces():
    assert (
        _find_cell_number(
            [
                "\n",
                "#     %%\n",
                "print('hello')\n",
                "print('wow!')",
                "# %%\n" "TARGET = True",
                "\n",
                "# %%",
                "# Too Far",
                "# Still too far",
            ],
            5,
        )
        == 1
    )
