'''
Test custom Django management commands.
'''
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
# SimpleTestCase wichtig weil TestCase die DB bereits beschreiben würde u.U.
from django.test import SimpleTestCase


# Decorater für die erstellte Funktion "wait_for_db" => Erbt aus BaseCommand die check-method
@patch('core.managment.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    '''Test commands.'''

    def test_wait_for_db_ready(self, patched_check):
        '''Test waiting for database if database ready.'''
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_witch(database=['default'])
        
    def test_wait_for_db_delay(self, patched_check):
