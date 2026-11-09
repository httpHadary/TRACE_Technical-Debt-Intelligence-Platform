package com.example.TechDept365.exception;

/** Thrown when an account has more repositories than the configured pagination limit allows. */
public class RepositoryLimitExceededException extends RuntimeException {

    private final int limit;

    public RepositoryLimitExceededException(int limit) {
        super("Account has more than " + limit + " repositories");
        this.limit = limit;
    }

    public int getLimit() {
        return limit;
    }
}
