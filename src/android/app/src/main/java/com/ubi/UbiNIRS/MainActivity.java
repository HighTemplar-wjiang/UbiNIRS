package com.ubi.UbiNIRS;

import android.app.DialogFragment;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.support.design.widget.FloatingActionButton;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.TypedValue;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.ubi.NanoScan.R;
import com.ubi.utils.DaoMaster;
import com.ubi.utils.DaoSession;
import com.ubi.utils.DbOpenHelper;
import com.ubi.utils.UbiNIRSApp;
import com.ubi.utils.UbiNIRSAppAdapter;
import com.ubi.utils.UbiNIRSAppDao;
import com.ubi.utils.UbiNIRSRequestQueue;

import org.greenrobot.greendao.database.Database;
import org.json.JSONException;
import org.json.JSONObject;

import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.List;

/**
 * This activity controls the main launcher view
 * This activity is responsible for generating the splash screen and the main
 * file list view
 *
 * From this activity, the user can begin the scan process {@link NewScanActivity},
 * Go to the info view {@link InfoActivity}
 *
 * @author collinmast
 */
public class MainActivity extends AppCompatActivity implements UbiNIRSAppConfigDialog.NoticeDialogListener{

    private static Context mContext;

    // Recycler view to show app list.
    private List<UbiNIRSApp> mUbiNIRSAppList;
    private RecyclerView mRecyclerView;
    private RecyclerView.Adapter mRecyclerViewAdacter;
    private RecyclerView.LayoutManager mRecyclerViewLayoutMananger;

    // Add NIRS app button.
    private FloatingActionButton mBtnAddNIRSApp;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mContext = this;
        setContentView(R.layout.activity_main);

        // Load the app list.
        // TODO: store/read the list metadata.
        mUbiNIRSAppList = new ArrayList<>();

        // Set up recycler view.
        mRecyclerView = findViewById(R.id.rv_applist);

        // Set layer manager.
        mRecyclerView.setLayoutManager(new LinearLayoutManager(this));

        // Specify adapter.
        mRecyclerViewAdacter = new UbiNIRSAppAdapter(mUbiNIRSAppList, this);
        mRecyclerView.setAdapter(mRecyclerViewAdacter);

        // Bind the adding button.
        mBtnAddNIRSApp = findViewById(R.id.fab_newapp);
        mBtnAddNIRSApp.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                showAppConfigDialog();
            }
        });
    }

    /*
     * When the activity is destroyed, make a call to the super class
     */
    @Override
    public void onDestroy() {
        super.onDestroy();
    }

    /* On resume, check for crashes and updates with HockeyApp,
     * and set up the file list,swipe menu, and event listeners
     */
    @Override
    public void onResume() {
        super.onResume();

        updateNIRSAppList();
    }

    /*
     * Inflate the options menu so that the info, settings, and connect icons are visible
     */
    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    /*
     * Handle the selection of a menu item.
     * In this case, there are three options. The user can go to the info activity,
     * the settings activity, or connect to a Nano
     */
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {

        int id = item.getItemId();

        if (id == R.id.action_settings) {
            Intent settingsIntent = new Intent(this, SettingsActivity.class);
            startActivity(settingsIntent);
            return true;
        }

        else if (id == R.id.action_info) {
            Intent infoIntent = new Intent(this, InfoActivity.class);
            startActivity(infoIntent);
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    /**
     * Function to convert dip to pixels
     *
     * @param dp the number of dip to convert
     * @return the dip units converted to pixels
     */
    private int dp2px(int dp) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, dp,
                getResources().getDisplayMetrics());
    }

    /**
     * Function to show the dialog for configuring NIRS App.
     */
    public void showAppConfigDialog() {
        DialogFragment dialog = new UbiNIRSAppConfigDialog();
        dialog.show(getFragmentManager(), "NoticeDialogFragment");
    }

    /**
     * Implement NIRS app config dialog methods.
     */
    @Override
    public void onDialogPositiveClick(DialogFragment dialog) {
        Spinner sp_httptype = dialog.getDialog().findViewById(R.id.sp_httptype);
        EditText et_address = dialog.getDialog().findViewById(R.id.et_address);
//        EditText et_port = dialog.getDialog().findViewById(R.id.et_port);

        // Get the inputs.
        String httptype = sp_httptype.getSelectedItem().toString();
        String url = et_address.getText().toString();
//        String port = et_port.getText().toString();

        // Complete URL.
        if (!url.startsWith("http")) {
            url = httptype + "://" + url;
        }

        addNIRSApp(url);
    }

    @Override
    public void onDialogNegativeClick(DialogFragment dialog) {
        // Do nothing if click cancel.
        dialog.getDialog().cancel();
    }

    /**
     * Add a NIRS app by requesting metadata from server.
     * @param url: Server url.
     */
    private void addNIRSApp(final String url) {
        String requestUrl = url.replaceFirst("/$", "") + "/metadata/";

        // Prepare request.
        JsonObjectRequest jsonObjectRequest = new JsonObjectRequest(
                Request.Method.GET, requestUrl, null, new Response.Listener<JSONObject>() {
            @Override
            public void onResponse(JSONObject response) {

                // Get metadata.
                try {
                    int appID = response.getInt("app_id");
                    String appName = response.getString("app_displayname");
                    String appDescription = response.getString("app_description");
                    String appProvider = response.getString("app_owner");
                    String appVersion = response.getString("app_version");
                    String appIconUrl = response.getString("app_icon");
                    String appThumbnail = response.getString("app_thumbnail");

                    // TODO: consider to use a better way to get the request URL.
                    String appServerAddress = url;

                    // Add server.
                    UbiNIRSApp newNIRSApp = new UbiNIRSApp(appID, appName, appProvider,
                            appDescription, appVersion, appServerAddress);

                    // Check existing server.
                    boolean isAppExist = false;
                    for (int i = 0; i < mUbiNIRSAppList.size(); i++) {
                        UbiNIRSApp currentNIRSApp = mUbiNIRSAppList.get(i);

                        if (currentNIRSApp.getAppID() == appID) {
                            // Update existing ID.
                            Toast.makeText(mContext, "App exists, updated.", Toast.LENGTH_SHORT).show();
                            isAppExist = true;
                            mUbiNIRSAppList.set(i, newNIRSApp);
                        }
                    }

                    // TODO: make a waiting circle.
                    if (!isAppExist) {
                        // Save config data.
                        Database db = new DbOpenHelper(mContext, getString(R.string.local_db_name)).getWritableDb();
                        DaoSession daoSession = new DaoMaster(db).newSession();
                        daoSession.insert(newNIRSApp);
                        db.close();
                    }

                    // Update card view.
                    updateNIRSAppList();
                }
                catch (JSONException e) {
                    Toast.makeText(mContext, "Server responded unexpected data.", Toast.LENGTH_SHORT).show();
                }
            }
        }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                Toast.makeText(mContext, "Server responded " + error.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });

        // Send request.
        UbiNIRSRequestQueue.getInstance(mContext).addToRequestQueue(jsonObjectRequest);

    }

    /**
     * Delete a NIRS app.
     * @param app_id: APP ID.
     */
    public void deleteNIRSApp(long app_id) {
        UbiNIRSAppDao ubiNIRSAppDao = new DaoMaster(new DbOpenHelper(
                this, getString(R.string.local_db_name)).getWritableDb())
                .newSession().getUbiNIRSAppDao();
        List<UbiNIRSApp> apps = ubiNIRSAppDao.queryBuilder()
                .where(UbiNIRSAppDao.Properties.AppID.eq(app_id)).list();
        if (apps.size() == 1) {
            ubiNIRSAppDao.delete(apps.get(0));
        }
        else {
            Toast.makeText(this,
                    MessageFormat.format(
                            "Cannot delete app with ID = {0}, {1} entities found.",
                            app_id, apps.size()),
                    Toast.LENGTH_SHORT).show();
        }
        updateNIRSAppList();
    }

    /**
     * Read local database to get the existing App list.
     */
    private void updateNIRSAppList() {
        DaoSession daoSession = new DaoMaster(new DbOpenHelper(
                this, getString(R.string.local_db_name)).getReadableDb()).newSession();
        List<UbiNIRSApp> ubiNIRSAppDaoList = daoSession.getUbiNIRSAppDao().loadAll();

        // Clear app list.
        mUbiNIRSAppList.clear();
        mRecyclerViewAdacter.notifyItemRangeRemoved(0, mUbiNIRSAppList.size());

        // Add all apps.
        mUbiNIRSAppList.addAll(ubiNIRSAppDaoList);
        mRecyclerViewAdacter.notifyDataSetChanged();
    }

}
