#!/usr/bin/python3
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pylint.lint import Run
from pylint_report.pylint_report import CustomJsonReporter
from pylint_report.pylint_report import main as report_main

from pre_commit_hooks.tools.pre_commit_tools import PreCommitTools

if TYPE_CHECKING:
    import argparse
    from collections.abc import Sequence

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class PylintHtmlReport(PreCommitTools):
    output_html: str
    output_json: str
    namesapace_args: argparse.Namespace
    pylint_args: list[str]

    def clean_json_report(self):
        if self.namesapace_args.output_json is None:
            logger.debug("clean json report")
            self.output_json.unlink()

    def convert_json_to_html(self):
        logger.debug("convert json to html")
        print([self.output_json.as_posix(), "-o", self.output_html.as_posix()])
        report_main(argv=[self.output_json.as_posix(), "-o", self.output_html.as_posix()])

    def create_parent_report(self, *, report_path: str) -> None:
        logger.debug(f"create {report_path.parent}")
        report_path.parent.mkdir(parents=True, exist_ok=True)

    def define_output_path(self, *, output_variable_name: str):
        logger.debug(f"define {output_variable_name}")
        value = self.namesapace_args.__dict__[output_variable_name]
        if isinstance(value, str):
            value = Path(value)
        if not value.is_absolute():
            output = Path().cwd() / value
        else:
            output = value
        self.create_parent_report(report_path=output.parent)
        return output

    def generate_ouptput_path(self):
        self.output_html = self.define_output_path(output_variable_name="output_html")
        self.output_json = self.define_output_path(output_variable_name="output_json")

    def get_args(self):
        logger.debug("parse arguments")
        self.namesapace_args, self.pylint_args = super().get_args()

    def run_pylint(self):
        logger.debug("run pylint")
        Run(self.pylint_args, exit=False)

    def set_params(self):
        logger.debug("define parser")
        super().set_params(help_msg='lint')
        self.parser.add_argument(
            '--output-html',
            action='store',
            help="path to folder to store html report",
            default=Path().cwd() / "html",
        )
        self.parser.add_argument(
            '--output-json',
            action='store',
            help="path to file to store json report",
            default=Path().cwd() / "pylint_report.json",
        )

    def update_pylint_args(self):
        logger.debug("update pylint args")
        self.pylint_args.extend(["--exit-zero", "--persistent=n", "--reports=n", "--score=n"])
        self.pylint_args.extend(
            [f"--output={self.output_json.as_posix()}", "--output-format=pylint_report.CustomJsonReporter"],
        )
        self.pylint_args.extend(self.namesapace_args.filenames)
        print(self.pylint_args)


def main(argv: Sequence[str] | None = None) -> int:
    instance = PylintHtmlReport()
    # instance.set_params()
    # instance.get_args()
    # instance.generate_ouptput_path()
    # instance.update_pylint_args()
    # instance.run_pylint()
    # instance.convert_json_to_html()
    # instance.clean_json_report()
    return instance.file_exist(file=instance.output_html) and not instance.file_empty(file=instance.output_html)


if __name__ == '__main__':
    raise SystemExit(main())
