import logging
import unittest

from etos_lib import ETOS
from environment_provider.splitter.split import Splitter


class TestSplitter(unittest.TestCase):
    """Test the environment provider slitter."""

    logger = logging.getLogger(__name__)

    def test_assign_iuts(self) -> None:
        """Test that that a test runner never gets 0 number of IUTs assigned.

        Approval criteria:
            - A test runner shall never had 0 number of IUTs assigned.

        Test steps::
            1. Assign IUTs to the provided test runners.
            2. Verify that no test runner get 0 assigned IUTs.
        """
        iuts = ["iut1", "iut2"]
        test_runners = {
            "runner1": {"iuts": {}, "unsplit_recipes": [1]},
            "runner2": {"iuts": {}, "unsplit_recipes": [2, 3, 4, 5]},
        }

        etos = ETOS("testing_etos", "testing_etos", "testing_etos")
        etos.config.set("TOTAL_TEST_COUNT", 5)
        etos.config.set("NUMBER_OF_IUTS", len(iuts))

        self.logger.info("STEP: Assign IUTs to the provided test runners.")
        _ = Splitter(etos, {}).assign_iuts(test_runners, iuts)

        self.logger.info("STEP: Verify that no test runner get 0 assigned IUTs.")
        for test_runner in test_runners.values():
            self.assertNotEqual(
                test_runner.get("number_of_iuts"),
                0,
                f"'number_of_iuts' is 0, test_runner got 0 assigned IUTs. {test_runner}]",
            )
