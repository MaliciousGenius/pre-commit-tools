#!/usr/bin/python3
from __future__ import annotations

import typing
from dataclasses import dataclass
from pathlib import Path

from pre_commit_hooks.tools.logger import logger
from pre_commit_hooks.tools.pre_commit_tools import PreCommitTools

if typing.TYPE_CHECKING:
    import re


@dataclass
class PatternDetection:
    commented: re.Match[bytes]
    disable_comment: re.Match[bytes]
    pattern: re.Match[bytes]

    def as_pattern(self, *, line):
        logger.debug(f'{line} | presence -> {bool(self.pattern.search(line))}')
        return bool(self.pattern.search(line))

    def is_commented(self, *, line):
        logger.debug(f'{line} | commented -> {bool(self.commented.search(line))}')
        return bool(self.commented.search(line))

    def is_disabled(self, *, line):
        logger.debug(f'{line} | disabled -> {bool(self.disable_comment.search(line))}')
        return bool(self.disable_comment.search(line))

    def detect(self, *, argv: Sequence[str] | None = None) -> int:
        tools_instance = PreCommitTools()
        args = tools_instance.set_params(help_msg='search print on python code', argv=argv)
        ret_val = 0
        for file in args.filenames:
            file = Path(file)
            with open(file) as stream:
                logger.debug(f'process file {file}')
                for line_number, line_content in enumerate(stream.readlines()):
                    if (
                        self.as_pattern(line=line_content)
                        and not self.is_disabled(line=line_content)
                        and not self.is_commented(line=line_content)
                    ):
                        print(f'[{file}][L.{line_number}] {line_content.strip()}')  # print-detection: disable
                        ret_val = 1
        return ret_val
