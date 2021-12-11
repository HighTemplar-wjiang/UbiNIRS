package com.ubi.utils;

import android.content.Context;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.support.annotation.NonNull;
import android.support.v4.content.ContextCompat;
import android.text.Html;
import android.text.Spannable;
import android.text.TextPaint;
import android.text.style.AbsoluteSizeSpan;
import android.text.style.URLSpan;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;
import com.ubi.NanoScan.R;
import com.ubi.UbiNIRS.NewScanActivity;

import org.json.JSONObject;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import me.saket.bettermovementmethod.BetterLinkMovementMethod;

public class UbiNIRSUtils {


    /**
     * Display HTML and customize url click events.
     * @param context: Activity context.
     * @param tv: TextView.
     * @param htmlString: Raw HTML string.
     */
    static public void setInteractiveTextViewFromHtml(final Context context, final TextView tv, final String htmlString) {

        // Request queue.
        final RequestQueue queue = Volley.newRequestQueue(context);

        // Build up spannable object.
        PicassoImageGetter imageGetter = new PicassoImageGetter(context, tv);
        Spannable spannableHtml;
        if (android.os.Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            spannableHtml = Spannable.Factory.getInstance().newSpannable(
                    Html.fromHtml(htmlString, Html.FROM_HTML_MODE_LEGACY, imageGetter, null));
        }
        else {
            spannableHtml = Spannable.Factory.getInstance().newSpannable(Html.fromHtml(htmlString));
        }

        // Set up link styles.
        URLSpan[] spans = spannableHtml.getSpans(0, spannableHtml.length(), URLSpan.class);
        for (int i = 0; i < spans.length; i++) {
            URLSpan span = spans[i];

            // Remove old span.
            int start = spannableHtml.getSpanStart(span);
            int end = spannableHtml.getSpanEnd(span);
            spannableHtml.removeSpan(span);

            // Add new span.
            span = new URLSpanInteractive(context, tv, queue, span.getURL());
            spannableHtml.setSpan(span, start, end, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
        tv.setText(spannableHtml);
        tv.setMovementMethod(BetterLinkMovementMethod.getInstance());
        tv.setClickable(false);
    }

    /**
     * Get host name from URL.
     * @param url
     * @return hostname.
     * @throws URISyntaxException
     */
    public static String getDomainName(String url) {
        URI uri;
        String domain = "";
        int port = -1;
        try{
            uri = new URI(url);
            domain = uri.getHost();
            port = uri.getPort();
        } catch (URISyntaxException e) {

        } finally {

        }

        if (port > 0){
            domain = domain + ":" + port;
        }
        return domain.startsWith("www.") ? domain.substring(4) : domain;
    }

    /**
     * Construct a URL string.
     * @param serverAddress: Server address, including port
     * @param urlPath: Path to the resource.
     * @param parameters: Parameters to request.
     * @return String: Restful API string.
     */
    static public String getRESTfulAPI(String serverAddress, String urlPath, Map<String, String> parameters) {
        String strAPI;

        // Find intrinsic parameters in url.
        String stemURL;
        String intrinsicParameters = "";
        if (urlPath.contains("?")){
            String[] separatedURL = urlPath.split("[?]");
            stemURL = separatedURL[0];
            intrinsicParameters = separatedURL[1].replaceFirst("/$", "");
        }
        else {
            stemURL = urlPath;
        }

        // Check http protocol.
        if (!serverAddress.startsWith("http")) {
            serverAddress = "http://" + serverAddress;
        }


        // Build a general URL as serverAddress/urlPath/ without double or missing slash.
        Uri.Builder uriBuilder = Uri.parse(
                new StringBuilder()
                        .append(serverAddress.replaceFirst("/$", ""))
                        .append("/")
                        .append(stemURL.replaceFirst("^/", "")
                                .replaceFirst("/$", "") + "/")
                        .toString()
        ).buildUpon();

        // Parameter handling.
        if ((parameters != null && parameters.size() > 0)) {
            // Add parameters.
            for (Map.Entry<String, String> entry: parameters.entrySet()) {
                uriBuilder.appendQueryParameter(entry.getKey(), entry.getValue());
            }
            strAPI = uriBuilder.toString();

            if (intrinsicParameters.length() > 0) {
                // Append intrinsic parameters.
                strAPI = strAPI + "&" + intrinsicParameters;
            }
        }
        else {

            strAPI = uriBuilder.toString();

            if (intrinsicParameters.length() > 0) {
                // Append intrinsic parameters.
                strAPI = strAPI + "?" + intrinsicParameters;
            }
            else {
                // Add ending-slash if there is not any parameter.
                strAPI = strAPI.endsWith("/") ? strAPI : strAPI + "/";
            }
        }

        return strAPI;
    }

    /**
     * Generic interactive listener.
     * @param context: Activity.
     * @param tv: TextView with interactive response.
     * @return: Response.Listener.
     */
    static public Response.Listener<String> getInteractiveResponseListener(final Context context, final TextView tv) {
        return new Response.Listener<String>() {
            @Override
            public void onResponse(String response) {
                // Check if can scan.
                Pattern canScanFinder = Pattern.compile("<meta name=\"nirs-can-scan\" content=\"(?<canScan>.*?)\">");
                Pattern statusFinder = Pattern.compile("<meta name=\"status\" content=\"(?<status>.*?)\">");
                Matcher canScanRegexMatcher = canScanFinder.matcher(response);
                Matcher statusRegexMatcher = statusFinder.matcher(response);

                Button buttonScan = ((NewScanActivity) context).findViewById(R.id.btn_scan);

                // Check if scannable.
                if (canScanRegexMatcher.find()) {

                    String canScan = canScanRegexMatcher.group(1);
                    Log.d("Network", "nirs-can-scan returns " + canScan);

                    // Set if "SCAN" button clickable.
                    if (canScan.equals("true")) {
                        buttonScan.setClickable(true);
                        buttonScan.setBackgroundColor(ContextCompat.getColor(context, R.color.kst_red));
                        buttonScan.setVisibility(View.VISIBLE);
                    }
                    else {
                        buttonScan.setClickable(false);
                        buttonScan.setBackgroundColor(ContextCompat.getColor(context, R.color.btn_unavailable));
                        buttonScan.setVisibility(View.INVISIBLE);
                    }

                }
                else {
                    buttonScan.setClickable(false);
                    buttonScan.setBackgroundColor(ContextCompat.getColor(context, R.color.btn_unavailable));
                    buttonScan.setVisibility(View.INVISIBLE);
                }

                // Check the status.
                if (statusRegexMatcher.find()) {

                    String status = statusRegexMatcher.group(1);
                    Log.d("Network", "status returns " + status);

                    // Generate new transaction number if status is final.
                    if (status.equals("final")) {
                        ((NewScanActivity) context).updateTransactionNumber();
                    }
                    else {
                        // TODO: set other status when update.
                    }

                }


                // Show new HTML file.
                UbiNIRSUtils.setInteractiveTextViewFromHtml(
                        context, tv, response);
            }
        };
    }

    /**
     * Generic interactive listener.
     * @param context: Context;
     * @param tv: Textview with interactive response.
     * @return: Response.ErrorListener.
     */
    static public Response.ErrorListener getInteractiveErrorListener(final Context context, final TextView tv) {
        return new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                Toast.makeText(context, "Server responded " + error.getMessage(), Toast.LENGTH_LONG).show();
            }
        };
    }

    /**
     * StringRequest that sends JSON object and returns raw strings.
     */
    static public class StringRequestJSON extends StringRequest {

        private String mBody;

        public StringRequestJSON(int method,
                                 String url,
                                 Response.Listener<String> listener,
                                 Response.ErrorListener errorListener,
                                 JSONObject jsonObject) {
            super(method, url, listener, errorListener);
            mBody = jsonObject.toString();
        }

        @Override
        public byte[] getBody() {
            return mBody.getBytes();
        }

        @Override
        public String getBodyContentType() {
            return "application/json";
        }
    }

    /**
     * Customized URL styles.
     */
    static public class URLSpanInteractive extends URLSpan {

        boolean mClicked;

        Context mContext;
        TextView mTextView;
        RequestQueue mQueue;

        public URLSpanInteractive(Context context, TextView tv, RequestQueue queue, String url) {
            super(url);

            mClicked = false;
            mContext = context;
            mTextView = tv;
            mQueue = queue;
        }

        @Override
        public void onClick(View view) {

            if(!mClicked) {
                mClicked = true;

                Map<String, String> parameters = ((NewScanActivity) mContext).getRequestParameters();

                String url = getRESTfulAPI(((NewScanActivity) mContext).getAppServerAddress(), getURL(), parameters);

                mQueue.add(new StringRequest(Request.Method.GET, url,
                        getInteractiveResponseListener(mContext, mTextView),
                        getInteractiveErrorListener(mContext, mTextView)));
            }
        }

        @Override
        public void updateDrawState(@NonNull TextPaint drawState) {
            super.updateDrawState(drawState);

            if (mClicked) {
                drawState.setUnderlineText(true);
            }
            else {
                drawState.setUnderlineText(false);
            }
//            drawState.setColor(ContextCompat.getColor(mContext, R.color.nir_red));
//            drawState.bgColor = Color.TRANSPARENT;
            drawState.setColor(Color.WHITE);
            drawState.bgColor = ContextCompat.getColor(mContext, R.color.nir_red);
            drawState.setTextSize(mContext.getResources().getDimension(R.dimen.link_font_size));
        }
    }
}
