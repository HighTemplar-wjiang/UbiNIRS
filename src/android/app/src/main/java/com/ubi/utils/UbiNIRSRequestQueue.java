package com.ubi.utils;

import android.content.Context;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.toolbox.Volley;

public class UbiNIRSRequestQueue {
    private static UbiNIRSRequestQueue instance;
    private RequestQueue requestQueue;
    private static Context ctx;

    private UbiNIRSRequestQueue(Context context) {
        ctx = context;
        requestQueue = getRequestQueue();
    }

    public static synchronized UbiNIRSRequestQueue getInstance(Context context) {
        if (instance == null) {
            instance = new UbiNIRSRequestQueue(context);
        }

        return instance;
    }

    public RequestQueue getRequestQueue() {
        if (requestQueue == null) {
            requestQueue = Volley.newRequestQueue(ctx.getApplicationContext());
        }
        return requestQueue;
    }

    public <T> void addToRequestQueue(Request<T> req) {
        getRequestQueue().add(req);
    }
}
