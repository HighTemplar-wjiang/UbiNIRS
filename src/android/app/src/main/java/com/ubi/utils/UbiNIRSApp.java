package com.ubi.utils;

import org.greenrobot.greendao.annotation.Entity;
import org.greenrobot.greendao.annotation.Id;
import org.greenrobot.greendao.annotation.NotNull;
import org.greenrobot.greendao.annotation.Generated;

@Entity
public class UbiNIRSApp {
    @Id
    public long appID;

    @NotNull
    public String appName;
    public String appProvider;
    public String appDescription;
    public String appVersion;
    public String appServerAddress;

    @Generated(hash = 1774178591)
    public UbiNIRSApp(long appID, @NotNull String appName, String appProvider,
            String appDescription, String appVersion, String appServerAddress) {
        this.appID = appID;
        this.appName = appName;
        this.appProvider = appProvider;
        this.appDescription = appDescription;
        this.appVersion = appVersion;
        this.appServerAddress = appServerAddress;
    }
    @Generated(hash = 404608344)
    public UbiNIRSApp() {
    }
    public long getAppID() {
        return this.appID;
    }
    public void setAppID(long appID) {
        this.appID = appID;
    }
    public String getAppName() {
        return this.appName;
    }
    public void setAppName(String appName) {
        this.appName = appName;
    }
    public String getAppProvider() {
        return this.appProvider;
    }
    public void setAppProvider(String appProvider) {
        this.appProvider = appProvider;
    }
    public String getAppServerAddress() {
        return this.appServerAddress;
    }
    public void setAppServerAddress(String appServerAddress) {
        this.appServerAddress = appServerAddress;
    }
    public String getAppDescription() {
        return this.appDescription;
    }
    public void setAppDescription(String appDescription) {
        this.appDescription = appDescription;
    }
    public String getAppVersion() {
        return this.appVersion;
    }
    public void setAppVersion(String appVersion) {
        this.appVersion = appVersion;
    }
}
