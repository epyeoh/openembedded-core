import unittest

class OeqaTestDiscover(object):

    def _discover_unittest_testsuite_testcase(self, test_dir):
        loader = unittest.TestLoader()
        testsuite_testcase = loader.discover(start_dir=test_dir, pattern='*.py')
        return testsuite_testcase

    def _generate_flat_list_of_unittest_testcase(self, testsuite):
        for test in testsuite:
            if unittest.suite._isnotsuite(test):
                yield test
            else:
                for subtest in self._generate_flat_list_of_unittest_testcase(test):
                    yield subtest

    def _get_testsuite_from_unittest_testcase(self, unittest_testcase):
        testsuite = unittest_testcase[unittest_testcase.find("(")+1:unittest_testcase.find(")")]
        return testsuite

    def _get_testcase_from_unittest_testcase(self, unittest_testcase):
        testcase = unittest_testcase[0:unittest_testcase.find("(")-1]
        testsuite = self._get_testsuite_from_unittest_testcase(unittest_testcase)
        testcase = '%s.%s' % (testsuite, testcase)
        return testcase

    def _get_testcase_list(self, unittest_testcase_list):
        testcase_list = []
        for unittest_testcase in unittest_testcase_list:
            testcase_list.append(self._get_testcase_from_unittest_testcase(str(unittest_testcase)))
        return testcase_list

    def get_oeqa_testcase_list(self, testcase_dir):
        unittest_testsuite_testcase = self._discover_unittest_testsuite_testcase(testcase_dir)
        unittest_testcase_list = self._generate_flat_list_of_unittest_testcase(unittest_testsuite_testcase)
        testcase_list = self._get_testcase_list(unittest_testcase_list)
        return testcase_list
