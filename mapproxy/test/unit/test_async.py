# This file is part of the MapProxy project.
# Copyright (C) 2011 Omniscale <http://omniscale.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import time
import threading
from mapproxy.util.async import imap_async_threaded, imap_async_eventlet, EventletPool, ThreadPool

from nose.tools import eq_
from nose.plugins.skip import SkipTest

class TestThreaded(object):
    def test_map(self):
        def func(x):
            time.sleep(0.05)
            return x
        start = time.time()
        result = list(imap_async_threaded(func, range(40)))
        stop = time.time()
        
        duration = stop - start
        assert duration < 0.2
        
        eq_(len(result), 40)
    
    def test_map_with_exception(self):
        def func(x):
            raise Exception()

        try:
            result = list(imap_async_threaded(func, range(40)))
        except Exception:
            pass
        else:
            assert False, 'exception expected'

try:
    import eventlet
    _has_eventlet = True
except ImportError:
    _has_eventlet = False

class TestEventlet(object):
    def setup(self):
        if not _has_eventlet:
            raise SkipTest('eventlet required')
    
    def test_map(self):
        def func(x):
            eventlet.sleep(0.05)
            return x
        start = time.time()
        result = list(imap_async_eventlet(func, range(40)))
        stop = time.time()
        
        duration = stop - start
        assert duration < 0.1
        
        eq_(len(result), 40)
    
    def test_map_with_exception(self):
        def func(x):
            raise Exception()

        try:
            result = list(imap_async_eventlet(func, range(40)))
        except Exception:
            pass
        else:
            assert False, 'exception expected'



class CommonPoolTests(object):
    def _check_single_arg(self, func):
        result = list(func())
        eq_(result, [3])
    
    def test_single_argument(self):
        f1 = lambda x, y: x+y
        pool = self.mk_pool()
        check = self._check_single_arg
        yield check, lambda: pool.map(f1, [1], [2])
        yield check, lambda: pool.imap(f1, [1], [2])
        yield check, lambda: pool.starmap(f1, [(1, 2)])
        yield check, lambda: pool.starcall([(f1, 1, 2)])
    
    
    def _check_single_arg_raise(self, func):
        try:
            result = list(func())
        except ValueError:
            pass
        else:
            assert False, 'expected ValueError'
    
    def test_single_argument_raise(self):
        def f1(x, y):
            raise ValueError
        pool = self.mk_pool()
        check = self._check_single_arg_raise
        yield check, lambda: pool.map(f1, [1], [2])
        yield check, lambda: pool.imap(f1, [1], [2])
        yield check, lambda: pool.starmap(f1, [(1, 2)])
        yield check, lambda: pool.starcall([(f1, 1, 2)])

    def _check_single_arg_result_object(self, func):
        result = list(func())
        assert result[0].result == None
        assert isinstance(result[0].exception[1], ValueError)
        
    def test_single_argument_result_object(self):
        def f1(x, y):
            raise ValueError
        pool = self.mk_pool()
        check = self._check_single_arg_result_object
        yield check, lambda: pool.map(f1, [1], [2], use_result_objects=True)
        yield check, lambda: pool.imap(f1, [1], [2], use_result_objects=True)
        yield check, lambda: pool.starmap(f1, [(1, 2)], use_result_objects=True)
        yield check, lambda: pool.starcall([(f1, 1, 2)], use_result_objects=True)


    def _check_multiple_args(self, func):
        result = list(func())
        eq_(result, [3, 5])
    
    def test_multiple_arguments(self):
        f1 = lambda x, y: x+y
        pool = self.mk_pool()
        check = self._check_multiple_args
        yield check, lambda: pool.map(f1, [1, 2], [2, 3])
        yield check, lambda: pool.imap(f1, [1, 2], [2, 3])
        yield check, lambda: pool.starmap(f1, [(1, 2), (2, 3)])
        yield check, lambda: pool.starcall([(f1, 1, 2), (f1, 2, 3)])
    
    def _check_multiple_args_with_exceptions_result_object(self, func):
        result = list(func())
        eq_(result[0].result, 3)
        eq_(type(result[1].exception[1]), ValueError)
        eq_(result[2].result, 7)
    
    def test_multiple_arguments_exceptions_result_object(self):
        def f1(x, y):
            if x+y == 5:
                raise ValueError()
            return x+y
        pool = self.mk_pool()
        check = self._check_multiple_args_with_exceptions_result_object
        yield check, lambda: pool.map(f1, [1, 2, 3], [2, 3, 4], use_result_objects=True)
        yield check, lambda: pool.imap(f1, [1, 2, 3], [2, 3, 4], use_result_objects=True)
        yield check, lambda: pool.starmap(f1, [(1, 2), (2, 3), (3, 4)], use_result_objects=True)
        yield check, lambda: pool.starcall([(f1, 1, 2), (f1, 2, 3), (f1, 3, 4)], use_result_objects=True)
    
    def _check_multiple_args_with_exceptions(self, func):
        result = func()
        eq_(result.next(), 3)
        try:
            result.next()
        except ValueError:
            pass
        else:
            assert False, 'expected ValueError'
    
    def test_multiple_arguments_exceptions(self):
        def f1(x, y):
            if x+y == 5:
                raise ValueError()
            return x+y
        pool = self.mk_pool()
        check = self._check_multiple_args_with_exceptions
        
        def check_pool_map():
            try:
                pool.map(f1, [1, 2, 3], [2, 3, 4])
            except ValueError:
                pass
            else:
                assert False, 'expected ValueError'
        yield check_pool_map
        yield check, lambda: pool.imap(f1, [1, 2, 3], [2, 3, 4])
        yield check, lambda: pool.starmap(f1, [(1, 2), (2, 3), (3, 4)])
        yield check, lambda: pool.starcall([(f1, 1, 2), (f1, 2, 3), (f1, 3, 4)])
    


class TestThreadPool(CommonPoolTests):
    def mk_pool(self):
        return ThreadPool()
    
    def test_base_config(self):
        # test that all concurrent have access to their
        # local base_config
        from mapproxy.config import base_config
        from mapproxy.util import local_base_config
        from copy import deepcopy

        # make two separate base_configs
        conf1 = deepcopy(base_config())
        conf1.conf = 1
        conf2 = deepcopy(base_config())
        conf2.conf = 2
        base_config().bar = 'baz'

        # run test in parallel, check1 and check2 should interleave
        # each with their local conf

        def check1(x):
            assert base_config().conf == 1
            assert 'bar' not in base_config()

        def check2(x):
            assert base_config().conf == 2
            assert 'bar' not in base_config()

        assert 'bar' in base_config()

        def test1():
            with local_base_config(conf1):
                pool1 = ThreadPool(5)
                list(pool1.imap(check1, range(200)))

        def test2():
            with local_base_config(conf2):
                pool2 = ThreadPool(5)
                list(pool2.imap(check2, range(200)))

        t1 = eventlet.spawn(test1)
        t2 = eventlet.spawn(test2)
        t1.wait()
        t2.wait()
        assert 'bar' in base_config()


import paste.util.threadinglocal
from paste.registry import StackedObjectProxy
from eventlet.corolocal import local
import mapproxy.config

class TestEventletPool(CommonPoolTests):
    def setup(self):
        if not _has_eventlet:
            raise SkipTest('eventlet required')
        
        # base_config()'s StackedObjectProxy uses a threaded local,
        # if thread.local was not monkey_patched before import
        # manualy patch for this test (pretty hacky)
        self.old_local = paste.util.threadinglocal.local
        paste.util.threadinglocal.local = local
        
        mapproxy.config.config._config = StackedObjectProxy(default=None)
    
    def mk_pool(self):
        return EventletPool()
    
    def teardown(self):
        # recreate StackedObjectProxy with threaded thread local
        paste.util.threadinglocal.local = self.old_local
        mapproxy.config.config._config = StackedObjectProxy(default=None)
    
    def test_base_config(self):
        # test that all concurrent have access to their
        # local base_config
        from mapproxy.config import base_config
        from mapproxy.util import local_base_config
        from copy import deepcopy

        # make two separate base_configs
        conf1 = deepcopy(base_config())
        conf1.conf = 1
        conf2 = deepcopy(base_config())
        conf2.conf = 2
        base_config().bar = 'baz'

        # run test in parallel, check1 and check2 should interleave
        # each with their local conf

        def check1(x):
            assert base_config().conf == 1
            assert 'bar' not in base_config()

        def check2(x):
            assert base_config().conf == 2
            assert 'bar' not in base_config()

        assert 'bar' in base_config()

        def test1():
            with local_base_config(conf1):
                pool1 = EventletPool(5)
                list(pool1.imap(check1, range(200)))

        def test2():
            with local_base_config(conf2):
                pool2 = EventletPool(5)
                list(pool2.imap(check2, range(200)))

        t1 = eventlet.spawn(test1)
        t2 = eventlet.spawn(test2)
        t1.wait()
        t2.wait()
        assert 'bar' in base_config()


class DummyException(Exception):
    pass

class TestThreadedExecutorException(object):
    def setup(self):
        self.lock = threading.Lock()
        self.exec_count = 0
        self.te = ThreadPool(size=2)
    def execute(self, x):
        time.sleep(0.005)
        with self.lock:
            self.exec_count += 1
            if self.exec_count == 7:
                raise DummyException()
        return x
    def test_execute_w_exception(self):
        try:
            self.te.map(self.execute, range(100))
        except DummyException:
            print self.exec_count
            assert 7 <= self.exec_count <= 10, 'execution should be interrupted really '\
                                               'soon (exec_count should be 7+(max(3)))'
        else:
            assert False, 'expected DummyException'

