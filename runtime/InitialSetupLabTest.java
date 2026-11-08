package com.wehavephones.mobile;

public final class InitialSetupLabTest {
    private static void require(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    public static void main(String[] args) {
        InitialSetupState ready = new InitialSetupState(false, true, true, true, true, false);
        require(ready.containerPrepared && ready.complete, "Direct Forever must not require Battle.net");
        require(!new InitialSetupState(false, false, true, true, true, false).complete,
                "Missing imagefs must remain blocked");
        require(!new InitialSetupState(false, true, false, true, true, false).complete,
                "Missing container must remain blocked");
        require(!new InitialSetupState(false, true, true, false, true, false).complete,
                "Incomplete profile preparation must remain blocked");
        require(!new InitialSetupState(false, true, true, true, false, false).complete,
                "Missing shortcuts must remain blocked");
        System.out.println("P11 Lab onboarding checks passed");
    }
}
