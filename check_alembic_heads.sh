HEADS=$(poetry run alembic heads | grep head | wc -l)
if [ $HEADS -gt 1 ]; then
    echo "ERROR: There are multiple alembic heads"
    poetry run alembic heads
    exit 1
fi
exit 0
