package com.ubi.utils;

import android.content.Context;

import org.apache.commons.lang3.NotImplementedException;
import org.greenrobot.greendao.database.Database;

public class DbOpenHelper extends DaoMaster.OpenHelper {

    public DbOpenHelper(Context context, String name) {
        super(context, name);
    }

    @Override
    public void onUpgrade(Database db, int oldVersion, int newVersion) {
        super.onUpgrade(db, oldVersion, newVersion);

        // TODO: implement database upgrade.
        throw new NotImplementedException("DbOpenHelper.onUpgrade not implemented.");
    }

}
