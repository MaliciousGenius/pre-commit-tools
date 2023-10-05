#!/usr/bin/python3
from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

from dockerfile_parse import DockerfileParser

from pre_commit_hooks.tools.pre_commit_tools import PreCommitTools

KEYWORDS_GROUP = ['ADD', 'ARG', 'COPY']

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

Line = NewType('Line', dict[str, int | str])

SHEBANG = '# syntax=docker/dockerfile:1.4'


# TODO: separate block for litteral ARGS and ARGS composed with variable
# TODO: order alphabeticly ARGS
# TODO: order alphabeticly ENV
# TODO: add config file support
@dataclass
class FormatDockerfile:
    dockerfile: Path = None
    content: str = ''
    parser: DockerfileParser = DockerfileParser()
    return_value: int = 0

    @staticmethod
    def _get_instruction(*, line: Line):
        logger.debug(f'get instuction type for {line}')
        return line['instruction']

    @staticmethod
    def _remove_split_lines(*, content):
        logger.debug('remove split lines ..........')
        return re.sub(r' \\\n +', ' ', content)

    def _as_header(self):
        line = self.parser.structure[0]
        return self._is_type(line=line, instruction_type='COMMENT') and SHEBANG in self._get_line_content(line=line)

    def _define_header(self):
        self._format_comment_line(index=-1, line_content=SHEBANG)

    def _file_as_changed(self):
        return repr(self.content) != repr(self.parser.content)

    def _format_comment_line(self, *, index, line_content):
        logger.debug('format COMMENT ..........')
        if index > 0:
            self.content += '\n'
        self.content += line_content

    def _format_env_line(self, *, line_content):
        logger.debug('format ENV ..........')
        multiline = ' \\\n    '.join(line_content.split(' ')[1:])
        self.content += '\n' + f'ENV {multiline}'

    def _format_from_line(self, *, index, line_content):
        logger.debug('format FROM ..........')
        if not self._is_same_as_previous(index=index):
            self.content += '\n' + '\n'
        self.content += line_content

    def _format_grouped_keyword_line(self, *, index, line_content):
        logger.debug('format grouped line ..........')
        if self._is_same_as_previous(index=index):
            logger.debug('same line ..........')
            self.content += line_content
        else:
            logger.debug('not same line ..........')
            if self.content.endswith('\n'):
                self.content = self.content.strip()
            self.content += '\n' + '\n' + line_content

    def _format_healthcheck_line(self, *, line_content):
        logger.debug('format HEALTHCHECK ..........')
        multiline = ' \\\n    CMD '.join(list(map(str.strip, line_content.split('CMD'))))
        self.content += '\n' + multiline

    def _format_run_line(self, *, index, line_content):
        logger.debug('format RUN ..........')
        line_content = line_content.replace('RUN ', '')
        if '&&' in line_content:
            data = ' \\\n    && '.join(list(map(str.strip, line_content.split('&&'))))
        else:
            data = ' \\\n    && ' + line_content
        if self._is_same_as_previous(index=index):
            self.content = self.content + data
        else:
            if data.startswith(' \\\n    && '):
                data = data.replace(' \\\n    && ', '', 1)
            self.content += '\n' + 'RUN ' + data

    def _format_simple(self, *, line: Line):
        logger.debug(f'format {self._get_instruction(line=line)} ..........')
        self.content += '\n\n' + self._get_line_content(line=line)

    def _get_line_content(self, *, line: Line):
        logger.debug(f'get line content {line} ..........')
        return line['content'].strip()

    def _is_grouped_keyword(self, *, line: Line) -> bool:
        logger.debug(f"test {line['instruction']} is a grouped keyword ..........")
        return self._get_instruction(line=line) in KEYWORDS_GROUP

    def _is_same_as_previous(self, *, index: int) -> bool:
        logger.debug(
            f"test if line {index} type {self.parser.structure[index-1]['instruction']} is same as previous {self.parser.structure[index]['instruction']} ..........",
        )
        print(
            f"test if line {index} type {self.parser.structure[index-1]['instruction']} is same as previous {self.parser.structure[index]['instruction']} ..........",
        )
        if index == 0:
            state = False
        else:
            state = self._get_instruction(line=self.parser.structure[index - 1]) == self._get_instruction(
                line=self.parser.structure[index],
            )
        return state

    def _is_type(self, *, line: Line, instruction_type: str) -> bool:
        logger.debug(f'check if line {line} is {instruction_type} ..........')
        return self._get_instruction(line=line) == instruction_type

    def format_file(self):
        logger.debug('format file')
        self.parser.content = self._remove_split_lines(content=self.parser.content)
        if self._as_header():
            self._format_comment_line(
                index=0,
                line_content=self._get_line_content(line=self.parser.structure[0]),
            )
            start = 1
        else:
            self._define_header()
            start = 0
        for index, line in enumerate(self.parser.structure[start:]):
            line_content = self._get_line_content(line=line)
            line_instruction = self._get_instruction(line=self.parser.structure[index])
            if index > 0:
                previous_line_instruction = self._get_previous_instruction(line=self.parser.structure[index])

            # if self._is_type(line=line, instruction_type='COMMENT'):
            #    self._format_comment_line(index=index, line_content=line_content)
            # elif self._is_type(line=line, instruction_type='ENV'):
            #     self._format_env_line(line_content=line_content)
            # elif self._is_type(line=line, instruction_type='FROM'):
            #    self._format_from_line(index=index, line_content=line_content)
            # elif self._is_type(line=line, instruction_type='RUN'):
            #     self._format_run_line(index=index, line_content=line_content)
            # elif self._is_type(line=line, instruction_type='HEALTHCHECK'):
            #     self._format_healthcheck_line(line_content=line_content)
            # elif self._is_grouped_keyword(line=line):
            #     self._format_grouped_keyword_line(index=index, line_content=line_content)
            # else:
            #     self._format_simple(line=line)

    def load_dockerfile(self, *, dockerfile_path: Path) -> None:
        logger.debug(f'read {dockerfile_path} ..........')
        self.parser.dockerfile_path = dockerfile_path
        with open(dockerfile_path) as stream:
            self.parser.content = stream.read()

    def save(self, *, file: Path) -> None:
        if self._file_as_changed():
            logger.debug(f'update {self.dockerfile} ..........')
            with open(file, 'w+') as stream:
                stream.seek(0)
                stream.write(self.content)
                stream.truncate()
            print(f'{file} .......... formatted')
            self.return_value = 1


def main(argv: Sequence[str] | None = None) -> int:
    format_dockerfile_class = FormatDockerfile()
    tools_instance = PreCommitTools()
    args = tools_instance.set_params(help_msg='format dockerfile', argv=argv)
    for file in args.filenames:
        file = Path(file)
        format_dockerfile_class.content = ''
        format_dockerfile_class.load_dockerfile(dockerfile_path=file)
        format_dockerfile_class.format_file()
        format_dockerfile_class.save(file=file)
        return format_dockerfile_class.return_value


if __name__ == '__main__':
    raise SystemExit(main())
