import json

import numpy as np
from PIL import Image

from splatplost.plot import get_loc_from_index, get_range, parse_coordinate


class RouteFile:
    def __init__(self, filename: str):
        """
        Parse a route file generated by splatplan. The correctness of the file is not checked as it is assumed that the file
        is generated internally.

        :param filename: The filename of the route file.
        """
        with open(filename, "r") as f:
            self.orig_file = json.load(f)

        self.vertical_divider: int = self.orig_file["divide_schedule"]["vertical_divider"]
        self.horizontal_divider: int = self.orig_file["divide_schedule"]["horizontal_divider"]

        self.blocks: dict[str, dict[str, list[str] | str]] = self.orig_file["blocks"]

        self.pixel = np.zeros((120, 320), dtype=np.uint8)

        for block in self.blocks:
            for point in self.blocks[block]["visit_route"]:
                x, y = parse_coordinate(point)
                self.pixel[x, y] = 1
        self.selected_blocks: set[int] = set()

    def select_block_from_pixel(self, x: int, y: int) -> None:
        block_idx = get_loc_from_index(x, y, self.horizontal_divider, self.vertical_divider)
        self.selected_blocks.add(block_idx)

    def deselect_block_from_pixel(self, x: int, y: int) -> None:
        block_idx = get_loc_from_index(x, y, self.horizontal_divider, self.vertical_divider)
        if block_idx in self.selected_blocks:
            self.selected_blocks.remove(block_idx)

    def get_selected_blocks(self) -> set[int]:
        """
        Get the selected blocks.

        :return: A set of selected blocks index.
        """
        return self.selected_blocks

    def select_all_blocks(self) -> None:
        """
        Select all blocks.

        """
        for i in range(self.horizontal_divider * self.vertical_divider):
            self.selected_blocks.add(i)

    def deselect_all_blocks(self) -> None:
        """
        De-select all blocks.

        """
        self.selected_blocks = set()

    @staticmethod
    def stain_rgb(original_color: tuple[int, int, int], stain: tuple[int, int, int]) -> tuple[int, int, int]:
        """
        Stain the original color with the stain color.

        :param original_color: The original color.
        :param stain: The stain color.
        :return: The stained color.
        """
        return (
            int(original_color[0] * 0.8 + stain[0] * 0.2),
            int(original_color[1] * 0.8 + stain[1] * 0.2),
            int(original_color[2] * 0.8 + stain[2] * 0.2)
            )

    def generate_image_of_selected(self) -> Image.Image:
        image: Image = Image.fromarray((1 - self.pixel) * 255, mode="L").convert("RGB")
        for block in self.selected_blocks:
            left_up_corner, right_down_corner = get_range(block, self.horizontal_divider, self.vertical_divider)
            # Alter the image to red
            for i in range(left_up_corner[0], right_down_corner[0]):
                for j in range(left_up_corner[1], right_down_corner[1]):
                    original_color = image.getpixel((j, i))
                    image.putpixel((j, i), self.stain_rgb(original_color, (255, 0, 0)))
            # Add border
            for i in range(left_up_corner[0], right_down_corner[0]):
                image.putpixel((left_up_corner[1], i), (0, 255, 0))
                image.putpixel((right_down_corner[1] - 1, i), (0, 255, 0))
            for j in range(left_up_corner[1], right_down_corner[1]):
                image.putpixel((j, left_up_corner[0]), (0, 255, 0))
                image.putpixel((j, right_down_corner[0] - 1), (0, 255, 0))
        return image
